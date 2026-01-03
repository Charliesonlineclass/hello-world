"""
SCORPION Multi-Tenant System - WordPress Integration
=====================================================

Helpers for integrating SCORPION with WordPress websites.
Generates configurations for Contact Form 7, WPForms, and custom plugins.

SCORPION Architecture Role:
    Part of integration layer
    Bridges WordPress sites with SCORPION legs

Features:
    - Contact Form 7 webhook configuration
    - WPForms webhook configuration
    - Custom WordPress plugin generation
    - Request validation
    - Lead normalization

Author: SCORPION System
Version: 1.0.0
"""

import json
import hmac
import hashlib
import secrets
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger("scorpion.wp")


@dataclass
class WebhookConfig:
    """Configuration for a webhook endpoint."""
    endpoint_url: str
    secret_key: str
    client_id: str
    form_type: str
    field_mappings: Dict[str, str]
    created_at: datetime

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        return data


class WPConnector:
    """
    WordPress Integration Connector for SCORPION.

    Provides helpers to connect WordPress websites with SCORPION
    client legs. Supports popular form plugins and custom integration.

    Supported Plugins:
    - Contact Form 7 (CF7)
    - WPForms
    - Gravity Forms
    - Custom PHP integration

    Usage:
        connector = WPConnector(base_url="https://api.scorpion.local")

        # Get CF7 webhook config
        cf7_config = connector.generate_cf7_webhook_config("j3_structural")

        # Generate custom plugin
        plugin_code = connector.generate_plugin_code("j3_structural")

        # Validate incoming request
        is_valid = connector.validate_wp_request(request, "secret123")
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        secrets_store: Optional[Dict[str, str]] = None
    ):
        """
        Initialize WordPress connector.

        Args:
            base_url: Base URL for SCORPION webhook API
            secrets_store: Optional store for webhook secrets
        """
        self.base_url = base_url.rstrip("/")
        self._secrets = secrets_store or {}

        # Endpoint paths for each client
        self._endpoints = {
            "j3_structural": "/webhook/j3/contact",
            "joe_ipc": "/webhook/joe/lead",
            "antonio_banking": "/webhook/antonio/application",
            "will_realestate": "/webhook/will/inquiry",
        }

        # Default field mappings for common form fields
        self._default_mappings = {
            "name": ["your-name", "name", "full_name", "customer_name"],
            "email": ["your-email", "email", "email_address"],
            "phone": ["your-phone", "phone", "tel", "telephone"],
            "message": ["your-message", "message", "comments", "inquiry"],
            "address": ["address", "your-address", "project_address"],
            "job_type": ["job-type", "service", "project_type"],
        }

        logger.info("WPConnector initialized")

    def _get_or_create_secret(self, client_id: str) -> str:
        """Get existing secret or create new one for a client."""
        if client_id not in self._secrets:
            self._secrets[client_id] = secrets.token_hex(32)
        return self._secrets[client_id]

    def generate_cf7_webhook_config(
        self,
        client_id: str
    ) -> Dict[str, Any]:
        """
        Generate Contact Form 7 webhook configuration.

        Returns instructions and code for setting up CF7 to
        send form submissions to SCORPION.

        Args:
            client_id: SCORPION client ID

        Returns:
            Configuration dictionary with setup instructions
        """
        endpoint = self._endpoints.get(client_id, "/webhook/contact")
        webhook_url = f"{self.base_url}{endpoint}"
        secret = self._get_or_create_secret(client_id)

        # CF7 form template
        form_template = '''
[text* your-name placeholder "Your Name"]

[email* your-email placeholder "Email Address"]

[tel your-phone placeholder "Phone Number"]

[textarea your-message placeholder "How can we help you?"]

[submit "Send Message"]
'''

        # PHP code to add to functions.php
        php_code = f'''
<?php
/**
 * SCORPION Integration for Contact Form 7
 * Client: {client_id}
 *
 * Add this code to your theme's functions.php or a custom plugin.
 */

add_action('wpcf7_mail_sent', 'scorpion_cf7_webhook');

function scorpion_cf7_webhook($contact_form) {{
    $submission = WPCF7_Submission::get_instance();
    if (!$submission) return;

    $data = $submission->get_posted_data();

    $payload = array(
        'name' => sanitize_text_field($data['your-name']),
        'email' => sanitize_email($data['your-email']),
        'phone' => sanitize_text_field($data['your-phone']),
        'message' => sanitize_textarea_field($data['your-message']),
        'source' => 'cf7_wordpress',
        'form_id' => $contact_form->id(),
        'timestamp' => current_time('c')
    );

    $json_payload = json_encode($payload);
    $secret = '{secret}';
    $signature = 'sha256=' . hash_hmac('sha256', $json_payload, $secret);

    $response = wp_remote_post('{webhook_url}', array(
        'headers' => array(
            'Content-Type' => 'application/json',
            'X-Webhook-Signature' => $signature
        ),
        'body' => $json_payload,
        'timeout' => 30
    ));

    if (is_wp_error($response)) {{
        error_log('SCORPION webhook error: ' . $response->get_error_message());
    }}
}}
?>
'''

        return {
            "client_id": client_id,
            "webhook_url": webhook_url,
            "secret_key": secret,
            "form_type": "contact_form_7",
            "form_template": form_template,
            "php_code": php_code,
            "instructions": [
                "1. Create a new Contact Form 7 form or edit existing",
                "2. Use the form template provided above",
                "3. Add the PHP code to your theme's functions.php",
                "4. Replace the secret key in production",
                "5. Test the form submission",
                "6. Check SCORPION dashboard for new leads"
            ]
        }

    def generate_wpforms_webhook_config(
        self,
        client_id: str
    ) -> Dict[str, Any]:
        """
        Generate WPForms webhook configuration.

        Args:
            client_id: SCORPION client ID

        Returns:
            Configuration dictionary with setup instructions
        """
        endpoint = self._endpoints.get(client_id, "/webhook/contact")
        webhook_url = f"{self.base_url}{endpoint}"
        secret = self._get_or_create_secret(client_id)

        # PHP code for WPForms integration
        php_code = f'''
<?php
/**
 * SCORPION Integration for WPForms
 * Client: {client_id}
 *
 * Add this code to your theme's functions.php or a custom plugin.
 */

add_action('wpforms_process_complete', 'scorpion_wpforms_webhook', 10, 4);

function scorpion_wpforms_webhook($fields, $entry, $form_data, $entry_id) {{

    // Map WPForms fields to SCORPION format
    $payload = array(
        'name' => '',
        'email' => '',
        'phone' => '',
        'message' => '',
        'source' => 'wpforms_wordpress',
        'form_id' => $form_data['id'],
        'entry_id' => $entry_id,
        'timestamp' => current_time('c')
    );

    // Extract field values by type
    foreach ($fields as $field) {{
        switch ($field['type']) {{
            case 'name':
                $payload['name'] = $field['value'];
                break;
            case 'email':
                $payload['email'] = $field['value'];
                break;
            case 'phone':
                $payload['phone'] = $field['value'];
                break;
            case 'textarea':
                $payload['message'] = $field['value'];
                break;
        }}
    }}

    $json_payload = json_encode($payload);
    $secret = '{secret}';
    $signature = 'sha256=' . hash_hmac('sha256', $json_payload, $secret);

    $response = wp_remote_post('{webhook_url}', array(
        'headers' => array(
            'Content-Type' => 'application/json',
            'X-Webhook-Signature' => $signature
        ),
        'body' => $json_payload,
        'timeout' => 30
    ));

    if (is_wp_error($response)) {{
        error_log('SCORPION webhook error: ' . $response->get_error_message());
    }}
}}
?>
'''

        return {
            "client_id": client_id,
            "webhook_url": webhook_url,
            "secret_key": secret,
            "form_type": "wpforms",
            "php_code": php_code,
            "instructions": [
                "1. Create your form in WPForms",
                "2. Include Name, Email, Phone, and Message fields",
                "3. Add the PHP code to your theme's functions.php",
                "4. Replace the secret key in production",
                "5. Test the form submission",
                "6. Check SCORPION dashboard for new leads"
            ]
        }

    def generate_plugin_code(self, client_id: str) -> str:
        """
        Generate a complete custom WordPress plugin.

        Creates a standalone plugin file that can be uploaded
        to WordPress for SCORPION integration.

        Args:
            client_id: SCORPION client ID

        Returns:
            Complete PHP plugin code
        """
        endpoint = self._endpoints.get(client_id, "/webhook/contact")
        webhook_url = f"{self.base_url}{endpoint}"
        secret = self._get_or_create_secret(client_id)
        plugin_name = f"SCORPION Integration - {client_id.replace('_', ' ').title()}"

        plugin_code = f'''<?php
/**
 * Plugin Name: {plugin_name}
 * Plugin URI: https://scorpion.local
 * Description: Connects this WordPress site to SCORPION CRM for {client_id}
 * Version: 1.0.0
 * Author: SCORPION System
 * License: Proprietary
 */

if (!defined('ABSPATH')) {{
    exit; // Exit if accessed directly
}}

class Scorpion_Integration {{

    private $client_id = '{client_id}';
    private $webhook_url = '{webhook_url}';
    private $secret_key = '{secret}';

    public function __construct() {{
        // Hook into form submissions
        add_action('wpcf7_mail_sent', array($this, 'handle_cf7_submission'));
        add_action('wpforms_process_complete', array($this, 'handle_wpforms_submission'), 10, 4);
        add_action('gform_after_submission', array($this, 'handle_gravity_submission'), 10, 2);

        // Add admin menu
        add_action('admin_menu', array($this, 'add_admin_menu'));

        // Add shortcode for chat widget
        add_shortcode('scorpion_chat', array($this, 'render_chat_widget'));
    }}

    /**
     * Send data to SCORPION webhook
     */
    private function send_to_scorpion($payload) {{
        $json_payload = json_encode($payload);
        $signature = 'sha256=' . hash_hmac('sha256', $json_payload, $this->secret_key);

        $response = wp_remote_post($this->webhook_url, array(
            'headers' => array(
                'Content-Type' => 'application/json',
                'X-Webhook-Signature' => $signature
            ),
            'body' => $json_payload,
            'timeout' => 30
        ));

        if (is_wp_error($response)) {{
            error_log('SCORPION Error: ' . $response->get_error_message());
            return false;
        }}

        $body = json_decode(wp_remote_retrieve_body($response), true);
        return $body;
    }}

    /**
     * Normalize form data to SCORPION format
     */
    private function normalize_payload($data, $source) {{
        return array(
            'name' => $this->extract_field($data, array('name', 'your-name', 'full_name')),
            'email' => $this->extract_field($data, array('email', 'your-email', 'email_address')),
            'phone' => $this->extract_field($data, array('phone', 'your-phone', 'tel')),
            'message' => $this->extract_field($data, array('message', 'your-message', 'comments')),
            'address' => $this->extract_field($data, array('address', 'your-address')),
            'source' => $source,
            'timestamp' => current_time('c'),
            'page_url' => wp_get_referer()
        );
    }}

    /**
     * Extract field value from various possible keys
     */
    private function extract_field($data, $possible_keys) {{
        foreach ($possible_keys as $key) {{
            if (isset($data[$key]) && !empty($data[$key])) {{
                return sanitize_text_field($data[$key]);
            }}
        }}
        return '';
    }}

    /**
     * Handle Contact Form 7 submission
     */
    public function handle_cf7_submission($contact_form) {{
        $submission = WPCF7_Submission::get_instance();
        if (!$submission) return;

        $data = $submission->get_posted_data();
        $payload = $this->normalize_payload($data, 'cf7_wordpress');
        $payload['form_id'] = $contact_form->id();

        $this->send_to_scorpion($payload);
    }}

    /**
     * Handle WPForms submission
     */
    public function handle_wpforms_submission($fields, $entry, $form_data, $entry_id) {{
        $data = array();
        foreach ($fields as $field) {{
            $data[$field['name']] = $field['value'];
        }}

        $payload = $this->normalize_payload($data, 'wpforms_wordpress');
        $payload['form_id'] = $form_data['id'];
        $payload['entry_id'] = $entry_id;

        $this->send_to_scorpion($payload);
    }}

    /**
     * Handle Gravity Forms submission
     */
    public function handle_gravity_submission($entry, $form) {{
        $data = array();
        foreach ($form['fields'] as $field) {{
            $data[$field->label] = rgar($entry, $field->id);
        }}

        $payload = $this->normalize_payload($data, 'gravity_wordpress');
        $payload['form_id'] = $form['id'];
        $payload['entry_id'] = $entry['id'];

        $this->send_to_scorpion($payload);
    }}

    /**
     * Add admin menu page
     */
    public function add_admin_menu() {{
        add_options_page(
            'SCORPION Integration',
            'SCORPION',
            'manage_options',
            'scorpion-integration',
            array($this, 'render_admin_page')
        );
    }}

    /**
     * Render admin settings page
     */
    public function render_admin_page() {{
        ?>
        <div class="wrap">
            <h1>SCORPION Integration</h1>
            <p>This site is connected to SCORPION CRM.</p>
            <table class="form-table">
                <tr>
                    <th>Client ID</th>
                    <td><code><?php echo esc_html($this->client_id); ?></code></td>
                </tr>
                <tr>
                    <th>Webhook URL</th>
                    <td><code><?php echo esc_html($this->webhook_url); ?></code></td>
                </tr>
                <tr>
                    <th>Status</th>
                    <td><span style="color: green;">Connected</span></td>
                </tr>
            </table>
            <h2>Chat Widget</h2>
            <p>Add the chat widget to any page using this shortcode:</p>
            <code>[scorpion_chat]</code>
        </div>
        <?php
    }}

    /**
     * Render chat widget shortcode
     */
    public function render_chat_widget($atts) {{
        $atts = shortcode_atts(array(
            'color' => '#2563eb',
        ), $atts);

        // Return chat widget HTML
        return '<div id="scorpion-chat" data-client="' . esc_attr($this->client_id) . '" data-color="' . esc_attr($atts['color']) . '"></div>';
    }}
}}

// Initialize plugin
new Scorpion_Integration();
?>
'''
        return plugin_code

    def validate_wp_request(
        self,
        request_body: bytes,
        secret: str,
        signature: str
    ) -> bool:
        """
        Validate an incoming WordPress webhook request.

        Args:
            request_body: Raw request body bytes
            secret: Webhook secret key
            signature: Signature from X-Webhook-Signature header

        Returns:
            True if valid, False otherwise
        """
        if not signature or not signature.startswith("sha256="):
            return False

        expected = "sha256=" + hmac.new(
            secret.encode(),
            request_body,
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(expected, signature)

    def format_wp_lead(self, wp_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize WordPress form data to SCORPION lead format.

        Args:
            wp_data: Raw WordPress form data

        Returns:
            Normalized lead dictionary
        """
        lead = {
            "name": "",
            "email": "",
            "phone": "",
            "message": "",
            "source": wp_data.get("source", "wordpress"),
            "custom_data": {}
        }

        # Map known fields
        for scorpion_field, wp_fields in self._default_mappings.items():
            for wp_field in wp_fields:
                if wp_field in wp_data and wp_data[wp_field]:
                    if scorpion_field in lead:
                        lead[scorpion_field] = wp_data[wp_field]
                    else:
                        lead["custom_data"][scorpion_field] = wp_data[wp_field]
                    break

        # Add any unmapped fields to custom_data
        mapped_fields = set()
        for fields in self._default_mappings.values():
            mapped_fields.update(fields)

        for key, value in wp_data.items():
            if key not in mapped_fields and key not in ["source", "timestamp"]:
                lead["custom_data"][key] = value

        return lead

    def get_installation_guide(self, client_id: str) -> str:
        """
        Get comprehensive installation guide for WordPress.

        Args:
            client_id: SCORPION client ID

        Returns:
            Markdown formatted installation guide
        """
        guide = f'''
# SCORPION WordPress Integration Guide
## Client: {client_id}

## Quick Start

### Option 1: Use the Custom Plugin (Recommended)

1. Download the plugin file from SCORPION dashboard
2. Go to WordPress Admin > Plugins > Add New
3. Click "Upload Plugin" and select the file
4. Activate the plugin
5. Go to Settings > SCORPION to verify connection

### Option 2: Manual Integration

#### For Contact Form 7:
1. Create your form in CF7
2. Add the webhook code to `functions.php`
3. Test form submission

#### For WPForms:
1. Create your form in WPForms
2. Add the webhook code to `functions.php`
3. Test form submission

## Adding the Chat Widget

Use the shortcode on any page or post:
```
[scorpion_chat]
```

Or add to your theme:
```php
<?php echo do_shortcode('[scorpion_chat]'); ?>
```

## Testing

1. Submit a test form on your website
2. Check SCORPION dashboard for new lead
3. Verify all fields are captured correctly

## Troubleshooting

### Form not sending to SCORPION
- Check webhook URL is correct
- Verify secret key matches
- Check server error logs

### Chat widget not appearing
- Clear browser cache
- Check for JavaScript errors in console
- Verify shortcode is properly placed

## Support

Contact SCORPION support for assistance.
'''
        return guide
