🚦 Votes Per Second (VPS) Monitor — Developer Feature
Overview
The FEZA Voting System’s live results dashboard now includes a Votes Per Second (VPS) Monitor for developers and authorized teachers. This feature provides real-time insights into voting activity, helping you assess system performance and detect issues instantly.

Key Metrics Displayed
Votes Per Second (Current)

Measures the voting rate over the most recent 10 seconds.
Updates every second for an instant snapshot.
Format: X.XX votes/s
Peak Rate (Last Minute)

Highest observed votes-per-second within the last 60 seconds.
Highlights the fastest voting surge.
Format: X.X votes/s
Average Rate (Last Minute)

Average voting rate across the previous 60 seconds.
Shows sustained system load.
Format: XX.XX votes/s
Example Display
Votes Per Second:       2.5 votes/s
Peak Rate (Last Min):   8.3 votes/s
Average Rate (Last Min): 3.7 votes/s
Who Can Access VPS Metrics?
Developers: Baraka Said, Ashley Charles
Teachers: Only with developer credentials
Location: Live Results dashboard (developer mode)
Technical Implementation
Vote timestamps are tracked in-memory (voteHistory array) on the client.
Metrics update every second (vpsUpdateInterval).
Automatic cleanup: Timestamps older than 60 seconds are discarded.
No server calls: All calculations are performed client-side for instant feedback.
Metrics reset when you:
Log out (vote history cleared)
Refresh the page (session resets, metrics start over)
Why Use the VPS Monitor?
Monitor System Health: Instantly spot high or low voting activity.
Detect Anomalies: Sudden dips or spikes could signal technical issues or peak participation.
Capacity Planning: Use peak rates to estimate maximum expected load.
Live Event Display: Great for projecting real-time participation during election events.
Notes & Behavior
All metrics start from 0.0 on login.
Metrics are session-based—refreshing the page resets statistics.
Only visible to users with developer access.
Tip:
For the most accurate monitoring, keep the dashboard open throughout the voting period—closing or refreshing resets the statistics.

Questions or feedback? Contact the FEZA Voting System developer team.

---

**Document Author:** Baraka Saidi Kiwanga


