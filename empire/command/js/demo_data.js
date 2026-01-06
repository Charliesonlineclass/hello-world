/* ═══════════════════════════════════════════════════════════════════
   SCORPION COMMAND CENTER - DEMO DATA
   Hardcoded data for offline demo
   ═══════════════════════════════════════════════════════════════════ */

const DEMO_DATA = {
    // 8 EYES - All Clients
    clients: [
        {
            id: 1,
            name: "JOE / IPC Solutions",
            industry: "Healthcare",
            accounts: 7,
            calls: 553,
            appts: 129,
            conv: "23%",
            mrr: 200,
            baby: "HERMES",
            status: "active"
        },
        {
            id: 2,
            name: "J3 Structural",
            industry: "Construction",
            accounts: 3,
            calls: 45,
            appts: 8,
            conv: "18%",
            mrr: 200,
            baby: "VULCAN",
            status: "active"
        },
        {
            id: 3,
            name: "ANTONIO",
            industry: "Banking",
            accounts: 1,
            calls: 45,
            appts: 12,
            conv: "27%",
            mrr: 500,
            baby: "MARCUS",
            status: "active"
        },
        {
            id: 4,
            name: "WILL",
            industry: "Real Estate",
            accounts: 1,
            calls: 78,
            appts: 15,
            conv: "19%",
            mrr: 100,
            baby: "HERMES",
            status: "active"
        },
        {
            id: 5,
            name: "CRUZ Roofing",
            industry: "Roofing",
            accounts: 2,
            calls: 0,
            appts: 0,
            conv: "N/A",
            mrr: 0,
            baby: "PAUSED",
            status: "paused"
        },
        {
            id: 6,
            name: "Empty Slot",
            status: "empty"
        },
        {
            id: 7,
            name: "Empty Slot",
            status: "empty"
        },
        {
            id: 8,
            name: "Empty Slot",
            status: "empty"
        }
    ],

    // JOE/IPC Accounts
    joeAccounts: [
        { id: 101, name: "NSIPA Healthcare", calls: 171, appts: 38, conv: "22%" },
        { id: 102, name: "Debt Consolidation", calls: 98, appts: 22, conv: "22%" },
        { id: 103, name: "Prescription Card", calls: 84, appts: 19, conv: "23%" },
        { id: 104, name: "Medicare Advantage", calls: 72, appts: 18, conv: "25%" },
        { id: 105, name: "Final Expense", calls: 58, appts: 15, conv: "26%" },
        { id: 106, name: "Auto Warranty", calls: 45, appts: 10, conv: "22%" },
        { id: 107, name: "Home Security", calls: 25, appts: 7, conv: "28%" }
    ],

    // J3 Projects
    j3Projects: [
        { id: 201, name: "Martinez Residence", type: "Renovation", status: "In Progress", value: "$45,000" },
        { id: 202, name: "Downtown Office", type: "Commercial", status: "Bidding", value: "$120,000" },
        { id: 203, name: "Lopez Addition", type: "Residential", status: "Completed", value: "$28,000" }
    ],

    // ANTONIO Accounts
    antonioAccounts: [
        { id: 301, name: "Banking Solutions", calls: 45, appts: 12, conv: "27%" }
    ],

    // WILL Accounts
    willAccounts: [
        { id: 401, name: "Real Estate Leads", calls: 78, appts: 15, conv: "19%" }
    ],

    // CRUZ Jobs
    cruzJobs: [
        { id: 501, name: "Smith Roof Repair", status: "Paused", value: "$8,500" },
        { id: 502, name: "Johnson Full Replacement", status: "Paused", value: "$22,000" }
    ],

    // NSIPA Healthcare Coordinators (Carlos's data)
    nsipaCoordinators: [
        { name: "Carlos Barahona", calls: 171, appts: 38, conv: 22.2, rank: 1 },
        { name: "Denisse Diaz", calls: 211, appts: 22, conv: 10.4, rank: 2 },
        { name: "Ana Mejia", calls: 226, appts: 36, conv: 15.9, rank: 3 },
        { name: "Edvaldo Espinoza", calls: 175, appts: 14, conv: 8.0, rank: 4 },
        { name: "Jesel Calderon", calls: 98, appts: 10, conv: 10.2, rank: 5 },
        { name: "Teresa Tovar", calls: 72, appts: 0, conv: 0.0, rank: 6, warning: true }
    ],

    // Lead Status for NSIPA
    nsipaLeadStatus: {
        red: 45,
        orange: 78,
        yellow: 34,
        green: 38,
        blue: 12
    },

    // Weekly Data
    weeklyData: {
        labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'],
        calls: [42, 55, 48, 52, 35],
        appts: [8, 12, 9, 11, 7]
    },

    // Sample Leads
    leads: [
        { id: 1, status: "green", name: "Maria Rodriguez", phone: "(555) 123-4567", coordinator: "Carlos Barahona", lastContact: "Today 2:30 PM", notes: "Appointment set for Monday" },
        { id: 2, status: "green", name: "John Smith", phone: "(555) 234-5678", coordinator: "Carlos Barahona", lastContact: "Today 11:15 AM", notes: "Very interested, confirmed appointment" },
        { id: 3, status: "yellow", name: "Robert Johnson", phone: "(555) 345-6789", coordinator: "Denisse Diaz", lastContact: "Yesterday", notes: "Callback requested for tomorrow" },
        { id: 4, status: "orange", name: "Lisa Williams", phone: "(555) 456-7890", coordinator: "Ana Mejia", lastContact: "2 days ago", notes: "Left voicemail, no response yet" },
        { id: 5, status: "red", name: "Mike Brown", phone: "(555) 567-8901", coordinator: "Edvaldo Espinoza", lastContact: "3 days ago", notes: "Not interested at this time" },
        { id: 6, status: "blue", name: "Sarah Davis", phone: "(555) 678-9012", coordinator: "Carlos Barahona", lastContact: "1 week ago", notes: "Follow up next month" },
        { id: 7, status: "green", name: "David Miller", phone: "(555) 789-0123", coordinator: "Carlos Barahona", lastContact: "Today 9:00 AM", notes: "Appointment confirmed" },
        { id: 8, status: "orange", name: "Jennifer Garcia", phone: "(555) 890-1234", coordinator: "Jesel Calderon", lastContact: "Yesterday", notes: "Voicemail left" },
        { id: 9, status: "yellow", name: "Chris Martinez", phone: "(555) 901-2345", coordinator: "Ana Mejia", lastContact: "Today 4:00 PM", notes: "Interested, needs more info" },
        { id: 10, status: "red", name: "Amanda Wilson", phone: "(555) 012-3456", coordinator: "Teresa Tovar", lastContact: "1 week ago", notes: "Wrong number" }
    ],

    // Call Log
    callLog: [
        { time: "4:45 PM", coordinator: "Carlos Barahona", lead: "Maria Rodriguez", duration: "12:34", result: "Appointment Set" },
        { time: "4:30 PM", coordinator: "Denisse Diaz", lead: "James Taylor", duration: "5:22", result: "Callback" },
        { time: "4:15 PM", coordinator: "Ana Mejia", lead: "Patricia Anderson", duration: "8:45", result: "Voicemail" },
        { time: "4:00 PM", coordinator: "Carlos Barahona", lead: "David Miller", duration: "15:20", result: "Appointment Set" },
        { time: "3:45 PM", coordinator: "Edvaldo Espinoza", lead: "Linda Thomas", duration: "3:10", result: "Not Interested" },
        { time: "3:30 PM", coordinator: "Jesel Calderon", lead: "Michael Jackson", duration: "7:55", result: "Callback" },
        { time: "3:15 PM", coordinator: "Carlos Barahona", lead: "Susan White", duration: "10:30", result: "Appointment Set" },
        { time: "3:00 PM", coordinator: "Ana Mejia", lead: "Richard Harris", duration: "4:20", result: "Voicemail" }
    ],

    // Empire Totals
    totals: {
        mrr: 1200,
        leads: 676,
        avgConv: "18.3%",
        babiesOnline: 10
    }
};

// Helper function to get client accounts based on client ID
function getClientAccounts(clientId) {
    switch(clientId) {
        case 1: return { type: 'accounts', data: DEMO_DATA.joeAccounts };
        case 2: return { type: 'projects', data: DEMO_DATA.j3Projects };
        case 3: return { type: 'accounts', data: DEMO_DATA.antonioAccounts };
        case 4: return { type: 'accounts', data: DEMO_DATA.willAccounts };
        case 5: return { type: 'jobs', data: DEMO_DATA.cruzJobs };
        default: return { type: 'accounts', data: [] };
    }
}

// Helper to get account details
function getAccountDetails(accountId) {
    // For demo, return NSIPA data for any account
    return {
        coordinators: DEMO_DATA.nsipaCoordinators,
        leadStatus: DEMO_DATA.nsipaLeadStatus,
        weeklyData: DEMO_DATA.weeklyData,
        leads: DEMO_DATA.leads,
        callLog: DEMO_DATA.callLog
    };
}
