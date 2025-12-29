"""
SCORPION-OTTER Meeting Bot
==========================

Full meeting processing pipeline: transcription → analysis → storage → notification.
Watch folders for automatic processing of new recordings.

Requirements:
    pip install openai-whisper chromadb watchdog
"""

import os
import json
import time
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Union, Callable
import logging
import threading

from .transcriber import transcribe_file, save_transcript, SUPPORTED_FORMATS
from .summarizer import full_analysis, analysis_to_markdown, save_analysis
from .notifier import send_email

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("OTTER.meeting_bot")

# ChromaDB configuration
CHROMADB_PATH = os.environ.get("CHROMADB_PATH", "./chromadb_meetings")


class MeetingBot:
    """
    Full meeting processing pipeline.

    Handles the complete workflow from audio file to searchable archive:
    1. Transcribe audio with Whisper
    2. Analyze transcript with LLM
    3. Store in ChromaDB for search
    4. Send notifications/follow-ups

    Usage:
        bot = MeetingBot()
        result = bot.process_recording("meeting.mp3")
        print(result['summary'])

        # Watch folder for new recordings
        bot.watch_folder("/recordings", callback=my_callback)
    """

    def __init__(
        self,
        whisper_model: str = 'base',
        llm_model: str = 'mistral',
        use_openai: bool = False,
        chromadb_path: str = CHROMADB_PATH,
        output_dir: str = "meeting_outputs"
    ):
        """
        Initialize MeetingBot.

        Args:
            whisper_model: Whisper model for transcription
            llm_model: LLM model for summarization
            use_openai: Use OpenAI instead of Ollama
            chromadb_path: Path for ChromaDB storage
            output_dir: Directory for output files
        """
        self.whisper_model = whisper_model
        self.llm_model = llm_model
        self.use_openai = use_openai
        self.chromadb_path = Path(chromadb_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        self._chroma_client = None
        self._collection = None
        self._watcher = None
        self._watching = False

        logger.info(f"MeetingBot initialized (Whisper: {whisper_model}, LLM: {llm_model})")

    def _get_chromadb(self):
        """Lazy load ChromaDB client and collection."""
        if self._chroma_client is None:
            try:
                import chromadb
                from chromadb.config import Settings

                self._chroma_client = chromadb.Client(Settings(
                    chroma_db_impl="duckdb+parquet",
                    persist_directory=str(self.chromadb_path),
                    anonymized_telemetry=False
                ))

                self._collection = self._chroma_client.get_or_create_collection(
                    name="meetings",
                    metadata={"hnsw:space": "cosine"}
                )

                logger.info(f"ChromaDB initialized at {self.chromadb_path}")

            except ImportError:
                logger.warning("ChromaDB not installed. Storage disabled. Run: pip install chromadb")
                return None, None

        return self._chroma_client, self._collection

    def process_recording(
        self,
        audio_path: Union[str, Path],
        meeting_name: Optional[str] = None,
        participants: Optional[List[str]] = None,
        notify_emails: Optional[List[str]] = None,
        save_outputs: bool = True
    ) -> Dict:
        """
        Process a complete meeting recording.

        Args:
            audio_path: Path to audio file
            meeting_name: Optional meeting name (auto-generated if None)
            participants: List of participant names
            notify_emails: Email addresses to send summary to
            save_outputs: Whether to save transcript and analysis files

        Returns:
            Complete processing result with transcript, analysis, paths
        """
        audio_path = Path(audio_path)

        if not meeting_name:
            meeting_name = audio_path.stem.replace("_", " ").replace("-", " ").title()

        logger.info(f"Processing meeting: {meeting_name}")
        start_time = datetime.now()

        result = {
            'meeting_name': meeting_name,
            'audio_file': str(audio_path),
            'participants': participants or [],
            'processed_at': start_time.isoformat(),
            'transcript': None,
            'analysis': None,
            'files': {},
            'chromadb_id': None,
            'notifications_sent': []
        }

        try:
            # Step 1: Transcribe
            logger.info("Step 1/4: Transcribing audio...")
            transcript_result = transcribe_file(
                audio_path,
                model_name=self.whisper_model
            )
            result['transcript'] = transcript_result

            if save_outputs:
                transcript_path = self.output_dir / f"{meeting_name.lower().replace(' ', '_')}_transcript.md"
                save_transcript(transcript_result, transcript_path, format='md')
                result['files']['transcript'] = str(transcript_path)

            # Step 2: Analyze
            logger.info("Step 2/4: Analyzing transcript...")
            analysis = full_analysis(
                transcript_result['text'],
                model=self.llm_model,
                use_openai=self.use_openai
            )
            result['analysis'] = analysis

            # Add convenience accessors
            result['summary'] = analysis.get('summary', '')
            result['action_items'] = analysis.get('action_items', [])
            result['decisions'] = analysis.get('decisions', [])
            result['executive_summary'] = analysis.get('executive_summary', '')

            if save_outputs:
                analysis_path = self.output_dir / f"{meeting_name.lower().replace(' ', '_')}_analysis.json"
                save_analysis(analysis, analysis_path)
                result['files']['analysis'] = str(analysis_path)

                # Also save markdown version
                md_path = self.output_dir / f"{meeting_name.lower().replace(' ', '_')}_analysis.md"
                md_path.write_text(analysis_to_markdown(analysis))
                result['files']['analysis_md'] = str(md_path)

            # Step 3: Store in ChromaDB
            logger.info("Step 3/4: Storing in ChromaDB...")
            chromadb_id = self.save_to_chromadb({
                'meeting_name': meeting_name,
                'transcript': transcript_result['text'],
                'summary': analysis.get('summary', ''),
                'action_items': analysis.get('action_items', []),
                'decisions': analysis.get('decisions', []),
                'participants': participants or [],
                'date': start_time.isoformat(),
                'duration': transcript_result.get('duration', 0)
            })
            result['chromadb_id'] = chromadb_id

            # Step 4: Send notifications
            if notify_emails:
                logger.info("Step 4/4: Sending notifications...")
                for email in notify_emails:
                    success = self._send_summary_email(email, result)
                    result['notifications_sent'].append({
                        'email': email,
                        'success': success
                    })
            else:
                logger.info("Step 4/4: No notifications configured, skipping...")

            elapsed = (datetime.now() - start_time).total_seconds()
            result['processing_time'] = elapsed
            logger.info(f"Meeting processed successfully in {elapsed:.1f}s")

        except Exception as e:
            logger.error(f"Error processing meeting: {e}")
            result['error'] = str(e)
            raise

        return result

    def _send_summary_email(self, email: str, result: Dict) -> bool:
        """Send meeting summary email."""
        subject = f"Meeting Summary: {result['meeting_name']}"

        body = f"""Meeting Summary
===============

Meeting: {result['meeting_name']}
Date: {result['processed_at']}
Duration: {result['transcript'].get('duration', 0):.0f} seconds

Executive Summary
-----------------
{result.get('executive_summary', 'Not available')}

Action Items
------------
"""
        for item in result.get('action_items', []):
            owner = f" ({item.get('owner', 'Unassigned')})" if item.get('owner') else ""
            body += f"• {item['action']}{owner}\n"

        body += """
Key Decisions
-------------
"""
        for decision in result.get('decisions', []):
            body += f"• {decision['decision']}\n"

        body += """
---
Generated by SCORPION-OTTER Meeting Bot
"""

        return send_email(email, subject, body)

    def save_to_chromadb(self, meeting_data: Dict) -> Optional[str]:
        """
        Save meeting data to ChromaDB for semantic search.

        Args:
            meeting_data: Meeting data dictionary

        Returns:
            Document ID in ChromaDB
        """
        _, collection = self._get_chromadb()

        if collection is None:
            logger.warning("ChromaDB not available, skipping storage")
            return None

        # Generate unique ID
        doc_id = hashlib.md5(
            f"{meeting_data['meeting_name']}_{meeting_data['date']}".encode()
        ).hexdigest()

        # Create searchable document
        document = f"""
Meeting: {meeting_data['meeting_name']}
Date: {meeting_data['date']}
Participants: {', '.join(meeting_data.get('participants', []))}

Summary:
{meeting_data.get('summary', '')}

Transcript:
{meeting_data.get('transcript', '')}
"""

        # Store with metadata
        collection.add(
            documents=[document],
            metadatas=[{
                'meeting_name': meeting_data['meeting_name'],
                'date': meeting_data['date'],
                'duration': meeting_data.get('duration', 0),
                'participants': json.dumps(meeting_data.get('participants', [])),
                'action_items': json.dumps(meeting_data.get('action_items', [])),
                'decisions': json.dumps(meeting_data.get('decisions', []))
            }],
            ids=[doc_id]
        )

        logger.info(f"Saved to ChromaDB with ID: {doc_id}")
        return doc_id

    def search_meetings(
        self,
        query: str,
        n_results: int = 5
    ) -> List[Dict]:
        """
        Search meeting archive semantically.

        Args:
            query: Search query
            n_results: Maximum number of results

        Returns:
            List of matching meetings with metadata
        """
        _, collection = self._get_chromadb()

        if collection is None:
            logger.warning("ChromaDB not available")
            return []

        results = collection.query(
            query_texts=[query],
            n_results=n_results
        )

        meetings = []
        for i, doc_id in enumerate(results['ids'][0]):
            metadata = results['metadatas'][0][i]
            meetings.append({
                'id': doc_id,
                'meeting_name': metadata.get('meeting_name'),
                'date': metadata.get('date'),
                'duration': metadata.get('duration'),
                'participants': json.loads(metadata.get('participants', '[]')),
                'action_items': json.loads(metadata.get('action_items', '[]')),
                'decisions': json.loads(metadata.get('decisions', '[]')),
                'relevance': results['distances'][0][i] if results.get('distances') else None
            })

        return meetings

    def watch_folder(
        self,
        folder_path: Union[str, Path],
        callback: Optional[Callable] = None,
        recursive: bool = False,
        notify_emails: Optional[List[str]] = None
    ):
        """
        Watch a folder for new audio files and process automatically.

        Args:
            folder_path: Folder to watch
            callback: Optional callback function(result) called after processing
            recursive: Watch subdirectories
            notify_emails: Emails to notify on new meetings
        """
        try:
            from watchdog.observers import Observer
            from watchdog.events import FileSystemEventHandler
        except ImportError:
            raise ImportError("watchdog not installed. Run: pip install watchdog")

        folder_path = Path(folder_path)
        folder_path.mkdir(exist_ok=True)

        bot = self

        class AudioHandler(FileSystemEventHandler):
            def on_created(self, event):
                if event.is_directory:
                    return

                path = Path(event.src_path)
                if path.suffix.lower() in SUPPORTED_FORMATS:
                    logger.info(f"New audio file detected: {path.name}")

                    # Wait for file to finish writing
                    time.sleep(2)

                    try:
                        result = bot.process_recording(
                            path,
                            notify_emails=notify_emails
                        )

                        if callback:
                            callback(result)

                    except Exception as e:
                        logger.error(f"Failed to process {path.name}: {e}")

        observer = Observer()
        observer.schedule(AudioHandler(), str(folder_path), recursive=recursive)
        observer.start()

        self._watcher = observer
        self._watching = True

        logger.info(f"Watching folder: {folder_path}")
        logger.info("Press Ctrl+C to stop watching...")

        try:
            while self._watching:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop_watching()

    def stop_watching(self):
        """Stop folder watching."""
        if self._watcher:
            self._watcher.stop()
            self._watcher.join()
            self._watcher = None
        self._watching = False
        logger.info("Stopped watching folder")

    def get_stats(self) -> Dict:
        """Get meeting processing statistics."""
        _, collection = self._get_chromadb()

        stats = {
            'chromadb_path': str(self.chromadb_path),
            'output_dir': str(self.output_dir),
            'whisper_model': self.whisper_model,
            'llm_model': self.llm_model,
            'total_meetings': 0
        }

        if collection:
            stats['total_meetings'] = collection.count()

        return stats


def process_meeting_cli():
    """CLI interface for meeting processing."""
    import sys

    if len(sys.argv) < 2:
        print("SCORPION-OTTER Meeting Bot")
        print("=" * 40)
        print()
        print("Usage:")
        print("  python meeting_bot.py <audio_file> [options]")
        print()
        print("Options:")
        print("  --name NAME        Meeting name")
        print("  --whisper MODEL    Whisper model (tiny/base/small/medium/large)")
        print("  --llm MODEL        LLM model for Ollama")
        print("  --notify EMAIL     Send summary to email")
        print("  --watch FOLDER     Watch folder for new recordings")
        print()
        print("Examples:")
        print("  python meeting_bot.py meeting.mp3")
        print("  python meeting_bot.py meeting.mp3 --name 'Team Standup'")
        print("  python meeting_bot.py --watch /recordings --notify team@example.com")
        sys.exit(1)

    # Parse arguments
    audio_file = None
    meeting_name = None
    whisper_model = 'base'
    llm_model = 'mistral'
    notify_email = None
    watch_folder = None

    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]

        if arg == '--name' and i + 1 < len(sys.argv):
            meeting_name = sys.argv[i + 1]
            i += 2
        elif arg == '--whisper' and i + 1 < len(sys.argv):
            whisper_model = sys.argv[i + 1]
            i += 2
        elif arg == '--llm' and i + 1 < len(sys.argv):
            llm_model = sys.argv[i + 1]
            i += 2
        elif arg == '--notify' and i + 1 < len(sys.argv):
            notify_email = sys.argv[i + 1]
            i += 2
        elif arg == '--watch' and i + 1 < len(sys.argv):
            watch_folder = sys.argv[i + 1]
            i += 2
        elif not arg.startswith('--'):
            audio_file = arg
            i += 1
        else:
            i += 1

    # Initialize bot
    bot = MeetingBot(
        whisper_model=whisper_model,
        llm_model=llm_model
    )

    # Watch mode
    if watch_folder:
        notify_list = [notify_email] if notify_email else None
        bot.watch_folder(watch_folder, notify_emails=notify_list)
        return

    # Process single file
    if not audio_file:
        print("Error: No audio file specified")
        sys.exit(1)

    notify_list = [notify_email] if notify_email else None
    result = bot.process_recording(
        audio_file,
        meeting_name=meeting_name,
        notify_emails=notify_list
    )

    # Print results
    print()
    print("=" * 60)
    print(f"MEETING PROCESSED: {result['meeting_name']}")
    print("=" * 60)
    print()
    print("EXECUTIVE SUMMARY:")
    print(result.get('executive_summary', 'Not available'))
    print()
    print("ACTION ITEMS:")
    for item in result.get('action_items', []):
        print(f"  • {item['action']}")
    print()
    print("KEY DECISIONS:")
    for decision in result.get('decisions', []):
        print(f"  • {decision['decision']}")
    print()
    print("OUTPUT FILES:")
    for name, path in result.get('files', {}).items():
        print(f"  {name}: {path}")
    print()
    print(f"Processing time: {result.get('processing_time', 0):.1f}s")
    print("=" * 60)


if __name__ == "__main__":
    process_meeting_cli()
