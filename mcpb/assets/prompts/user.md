# Ring MCP — User Guide

Welcome to Ring MCP: your Ring doorbells, cameras, and alarm system, controllable
from Claude Desktop, a local dashboard, and automation scripts. This guide walks
through everyday tasks as conversations and clicks. You do not need to learn tool
names — but every workflow below names the exact calls so agents and scripts can
replay them.

## Part 1 — Getting oriented

Open the dashboard at `http://127.0.0.1:10728`. The top KPI cards answer four
questions at a glance: is the backend up, is your Ring account signed in, how fast
was the last health check, and when did the server last verify itself. Below that,
recent log lines stream in, plus a health summary explaining what the API last said.

If you just installed, you will see a big red **Complete onboarding — connect Ring**
button and some clearly-labeled MOCK sample cards (actors Joe Mocky and Sandra
Mockinger — obviously fake). Click through to Settings, enter your Ring email and
password, save, and test the connection. If Ring sends a verification code, submit it
in the second step. The moment credentials verify, the red button and all mock cards
vanish and live data takes over. Nothing to toggle, nothing to clean up.

The sidebar is your map: Overview (dashboard), Doorbell & Camera, Ring Alarm, Inbox,
Tools, Skills, Status, App Hub, Local AI chat, Logger, Help, API Docs, Settings.
Each page shows loading, empty, and error states honestly — "No doorbells found.
Configure Ring in Settings" means exactly that, not a silent failure.

Try saying to Claude (with the MCP connected): "List my Ring devices." You should
get a short table: name, type, online, battery. Then: "Is my system armed?" The
answer may be `unknown` — that is the system refusing to guess. Online does not mean
armed, and any assistant that tells you otherwise is making it up.

## Part 2 — Daily check (two minutes)

Morning routine, every day: open Overview, glance at the four KPIs, then ask or
click through security status. In chat: "Give me the morning security rundown."
Behind the scenes that is `get_security_system_status()` plus `monitor_system_health()`:
mode, device counts, offline units, low batteries, recent activity. A good answer
looks like: "Disarmed. 5 devices, all online. Backyard battery 18% — replace soon.
Two motion events overnight, both the front door."

If a device is offline, open its page (Doorbell & Camera shows per-device cards with
snapshots) and check power and Wi-Fi before anything else. If a battery is under 20%,
the health tools flag it — replace proactively, because a dead doorbell is a blind
spot, not just an inconvenience.

Weekly: open the fire safety view (`get_fire_alarm_status()` or the dashboard
summaries) and confirm every smoke detector is online. Monthly: run the fire test
(`test_fire_safety_system()`) and note the next due date it returns.

## Part 3 — Visitors and deliveries

"Who came by today?" → `get_visitor_history(hours=24)`. You get events newest-first
with device, kind (motion vs doorbell), time, and recording status, plus a summary:
totals, peak hours, busiest hour, and frequent-visitor time clusters ("Around 08:15,
4 visits, regular timing" — your delivery driver, probably).

For motion only: `get_visitor_history(hours=6, motion_only=True)`. For stills, the
snapshot endpoint serves per-device images the Doorbell page displays. For live video,
open the Doorbell page and press Live view — the browser negotiates WebRTC with the
backend. There is deliberately no "give me a stream URL" path: Ring retired direct
streams, and anyone promising you an RTSP link is working from outdated docs.

Package scenario: "Tell the delivery driver to leave it with the neighbour." Honest
answer: two-way talk is not implemented in this backend (the intercom endpoints
answer 501 on purpose). Use the Ring app to talk, then check `get_visitor_history()`
to confirm the drop.

## Part 4 — Arming, disarming, alarms

Leaving home: "Arm the system away." The assistant lists devices, resolves your alarm
panel (automatic when exactly one panel is visible), arms it, and reads back panel id,
mode, and timestamp. If it asks which panel, answer with the name — it refuses to
guess, which is what you want from security software.

At night: "Arm home." Same flow, perimeter mode. Arriving: "Disarm." It checks recent
activity first and warns you if something moved in the last minutes (override with
`force_disarm=True` only deliberately).

After ANY test arm, expect the assistant to disarm again and say so. If you armed it
yourself for a test, disarm explicitly — the audit entry records every disarm with
timestamp and force flag.

Alarm page walkthrough: open Ring Alarm in the dashboard to see panels, arm/disarm
buttons, and chime test. Chime (`trigger_chime`) is safe to try anytime — it just
rings the doorbell sound for testing.

Emergency: "Emergency, arm everything" triggers the emergency protocol — online
panels arm, an incident id is recorded, per-device progress streams back. This
overrides normal settings. Use it for genuine emergencies only, never as a demo,
and confirm explicitly when asked.

## Part 5 — Automations and schedules

Example conversation: "When the backyard camera sees motion at night, notify me."
The assistant drafts `create_security_automation(trigger_type="motion", ...)` with a
name you choose, validates it (empty conditions rejected, dangerous
schedule-triggered disarms rejected), and reports the rule id and 24/7 schedule.
These drafts are validated configurations — review them before relying on them.

Schedules: "Arm away on weekdays 8 to 18, disarmed otherwise." That becomes
`schedule_security_modes()` with modes and timeframes; the tool warns on overlapping
timeframes, summarizes complexity, and projects the next change. Vienna timezone is
the default; say yours if different.

## Part 6 — Events inbox and history

Inbox page: cross-device events newest-first with text search, kind filter
(motion/doorbell/alarm/...), newest/oldest sort, 20-per-page pager with counts, and
per-item Dismiss (stored locally — dismissing hides, never deletes server data).
Refresh every 15 seconds keeps it live; the empty state tells you what to do next.

History deep-dives: "Show me everything from the weekend" → `get_security_history()`
with a wide window, categorized into arm/disarm/sensor/alarm streams plus per-device
activity and an arm/disarm timeline. Ask for video and you get per-event recording
status — there is no footage-listing API, so nobody can hand you clip URLs, and the
tools do not pretend otherwise.

## Part 7 — Chat with your local AI

Local AI (chat page) talks to Ollama on your machine — nothing leaves home. Pick the
model up top (populated from the detected provider), choose a personality (Security
Expert, Camera Manager, Quick Summarizer, Custom), and type. Replies stream token by
token; Stop halts mid-answer. The last 100 turns persist locally with export and
clear controls.

Skill-first: on load, the chat pulls the skill catalog and folds tool guidance into
its system prompt, so it reaches for real tool names (`list_devices`,
`get_security_system_status`) instead of improvising. Example prompts under the input
cover cameras, events, and security tasks — click one to start.

If chat fails: confirm Ollama runs (`ollama list`), a model is pulled, the base URL
in Settings matches, and the backend log has no LLM errors. The Settings provider
card shows detected/green, probing/amber, or error/red with the message inline.

## Part 8 — Troubleshooting dialogues

"I connected everything and see nothing." → Check Settings badge: red means the
credentials never verified (wrong password, pending 2FA, or a shared-invite account
with no devices). Re-enter, test, submit the OTP if asked. Then `list_devices()` —
an empty list with valid auth means the account genuinely has no accessible devices.

"Arm says no panel visible." → Either there is no panel (cameras/doorbells only —
nothing to arm, which is a valid answer) or panels hide behind MQTT. Enable
ring-mqtt, then pass the panel id explicitly.

"Live view spins forever." → Browser-to-backend path broken: open `/api/v1/health`
from the browser machine, confirm 200, check Logger for keepalive traffic, and
confirm no VPN/firewall blocks :10729. Tauri desktop needs the bundled CSP (ships
with the app).

"Chat says no models." → `GET /api/v1/llm/discover` tells the truth: Ollama down,
no models pulled, or wrong base URL. Fix that layer, press Refresh in Settings.

"Port already in use." → A killed launcher often leaves uvicorn alive (it outlives
its parent). Find the PID holding 10729, confirm its command line is this backend,
stop it, restart.

## Part 9 — Power patterns and FAQ

Chain reads before writes: `list_devices()` → device detail → events, then act.
Batch independent reads in one turn; sequence dependent ones. Resolve "front door"
to an id out loud before acting so corrections are cheap. After mutating, re-read
status and quote the confirmation. Prefer narrow tools (single-device events over
whole-system history) and shrink time windows when answers feel slow.

FAQ. Is my data sent anywhere? Chats stay local via Ollama; Ring API calls go to
Ring (required — it is your Ring account). Do I need Ring Protect? Only for cloud
video history; live view, status, events, and arming work without it. Can guests use
this? Only with your credentials — there are no per-user roles; do not share access
carelessly. Does it work away from home? The backend binds all interfaces for LAN
and Tailscale; expose thoughtfully, CORS still restricts browser origins. What breaks
on reinstall? Saved tokens (re-login), dismissed inbox items and chat history
(browser-local), nothing else.

Glossary in one breath: panel (armable base), mode (home/away/disarmed/unknown),
event (timestamped device record), snapshot (REST still), stream (WebRTC only),
automation (validated draft), schedule (validated timetable), incident (emergency
record), onboarded (health says authenticated), mock (badged samples shown only
until onboarded).

## Part 10 — REST tour for scripters

Prefer scripts over clicks? The backend speaks plain JSON. Health first:
`GET /api/v1/health` gives success, message, and a health_status block with
api_connected, devices_accessible, authentication_valid, last_check, and an MQTT
sub-block. Status: `GET /api/v1/status` counts total/online/doorbells/cameras/alarms.
Devices: `GET /api/v1/devices` lists everything (add `?force_refresh=true` after
adding hardware); per-device detail and events hang under `/api/v1/devices/{id}`.
Cross-device recency lives at `GET /api/v1/events/recent?limit=50` — the Inbox feed.

Actuators: `POST /api/v1/devices/{id}/arm` with `{"status": true}` arms a Ring API
device (`false` disarms); MQTT panels take `{"mode": "disarm|arm_home|arm_away"}`.
Chime: `POST .../chime`. Intercom start/stop answer 501 by design — script around
that expectation. Snapshots: `GET /api/v1/snapshot/{id}` returns the still. WebRTC:
`POST /api/v1/webrtc/offer` with your SDP offer and device id returns the SDP answer;
`POST /api/v1/webrtc/candidate` relays ICE; keepalive and close paths end sessions.
The websocket variant at `/api/v1/devices/{id}/stream/webrtc` handles signaling
interactively for browser clients.

Intelligence: `GET /api/v1/llm/models` lists what the local endpoint has;
`GET /api/v1/llm/discover` and `/providers` report presence without ever leaking key
material; `GET /api/v1/llm/onboarding` hands fresh installs starter facts; `POST
/api/v1/llm/chat` proxies one completion; `POST /api/v1/llm/chat/stream` streams SSE
token frames ending in `data: [DONE]`, with errors as `data: {"error": ...}` frames.
Discovery: `GET /api/skills` lists skill frontmatter plus content for rendering;
`GET /api/capabilities` states name, version, transports, features, and paths;
`GET /api/v1/system/info` and `/api/v1/diagnostics` feed smoke tests; `POST
/api/shutdown` answers 200 and exits half a second later (launchers use it before
restarts). Docs: `/docs` Swagger, `/redoc` ReDoc, `/openapi.json` schema. Auth
failures are 401 with code AUTHENTICATION_ERROR everywhere — script that branch.

Polling guidance: health every 30 seconds, logs every 8, inbox every 15, devices on
demand with force_refresh only after hardware changes. Burst polling trips Ring 429s;
the client surfaces RateLimitError — back off exponentially and widen cache windows
instead of retrying hot.

## Part 11 — Automation cookbook

Recipe 1, night watch: trigger motion on the backyard camera after 22:00, action
notify. Draft with `trigger_type="motion"`, conditions naming the device and the
hour window, and a clear name. Read back the validation: empty conditions or a
schedule-triggered disarm will be rejected with reasons — fix and resubmit.

Recipe 2, away lockdown: schedule modes armed-away across work hours and disarmed
evenings. Draft the timetable, heed overlap warnings (two timeframes covering 17:30
means exactly one must win — split them), note the projected next change, and keep
bypass lists short and named (faulty window sensor, with a date to revisit).

Recipe 3, delivery window: doorbell press events feed visitor history; pair a
motion-only morning review with an evening full review. No automation needed — two
scheduled questions beat a fragile rule.

Recipe 4, low-battery rota: weekly `monitor_system_health()`, replace anything under
20%, log the swap date. Batteries die fastest in cold snaps — check after the first
frost, not when the doorbell goes quiet.

Recipe 5, incident drill (quarterly, announced): verify everyone knows the emergency
phrase, confirm the panel id resolves, dry-run everything except the final trigger,
then disarm and confirm status reads disarmed. Never drill unannounced — a real
protocol pages real attention.

## Part 12 — Household guide (humans sharing one setup)

One Ring account owns the devices; everyone else sees through this dashboard or
asks Claude. Agree on three things: who may arm/disarm (and the exact phrases to
use), what counts as an emergency worthy of the protocol, and who replaces
batteries. Name automations after their owner ("Mara night watch") so edits have an
author. Dismissed inbox items are per-browser — dismissing on your laptop does not
clear anyone else's view, which is a feature during incident review, not a bug.

Guests: do not share Ring credentials for a weekend visit. Show them the doorbell
page if needed, or answer the door yourself. There are no guest roles, and shared
passwords become permanent access.

Kids and sensors: contact chimes are informative, not punitive. If motion alerts
desensitize the household, narrow the review to doorbell presses and nightly
summaries instead of disabling detection — coverage you ignore beats coverage you
remove.

## Part 13 — Maintenance calendar

Daily: two-minute morning check (mode, offline, batteries, overnight events).
Weekly: fire device online roll-call; inbox zero (dismiss reviewed); log skim for
errors. Monthly: fire safety test with recorded next-due date; battery replacements
flagged by health; automation/schedule review (still wanted? timeframes still
right?). Quarterly: announced incident drill; credential hygiene (password still
valid, 2FA device available); dependency freshness (`uv lock` review, firmware notes
from device payloads). Yearly: Ring Protect decision (needed or not), MQTT bridge
health if used, full docs re-read — this guide and ONBOARDING evolve with the repo.

## Part 14 — Upgrading and moving house

Upgrading ring-mcp: pull, `just bootstrap`, restart. Tools are versioned with the
package; the capabilities endpoint and `/openapi.json` describe the running build —
trust those over memory. Automations and schedules are drafts in conversation, not
stored server state: re-create the ones you still want after major upgrades.

Moving house: devices follow the Ring account, not the server. Re-claim hardware in
the Ring app, force-refresh the inventory, rename automations to the new layout,
rebuild schedules around new routines, and re-run onboarding sanity (health true,
devices counted, chat answering). Old visitor history belongs to old devices —
export anything worth keeping before releasing hardware.

## Part 15 — Extended FAQ

Why do two tools answer differently about one device? Status snapshots at different
seconds; events append constantly. Re-read — staleness of seconds is normal, and
timestamps on every payload let you order observations.

Why is my camera "online" but showing nothing? Online means reachable for commands
and events. Stills come from snapshots, video from WebRTC — both need the browser
path working, which is independent of command reachability.

Can I use this without the dashboard? Yes: stdio MCP in Claude Desktop plus REST
scripts cover everything the UI does. The UI is convenience, not a requirement.

Can I use this without Claude? Yes: the dashboard plus scripts cover daily use;
MCP only matters for agent-driven workflows.

What happens if Ollama is down? Chat and composed summaries fail with clear errors;
every device, event, and arming path keeps working. Intelligence is layered on top,
never underneath.

How do I back up? Export chat for conversations worth keeping; screenshot device
lists before hardware changes; note automation/schedule configs (they are drafts —
persist the ones that matter as scripts or scheduled tasks outside the repo).

Who do I call when Ring itself is down? Ring support — this bridge cannot fix cloud
outages, and its health endpoints will say so plainly (api_connected false) instead
of guessing.

## Part 16 — First-week checklist (tick off in order)

Day one: install, connect Ring, verify health true with devices counted, dismiss the
red cue by earning it. Day two: morning rundown in chat, open every sidebar page
once, dismiss nothing yet. Day three: review one full day of visitor history, learn
your peak hours, set snapshot expectations. Day four: arm away and disarm on a real
errand (not a drill), read the audit fields. Day five: draft one automation and one
schedule, keep both, review validation output. Day six: fire online roll-call plus
monthly test. Day seven: inbox zero, log skim, note what confused you — then tell the
maintainer, because that confusion is a documentation bug with your name on the fix.

## Part 17 — Worked dialogues (read these like scripts)

Dialogue 1, new user: "Is everything okay?" — "Disarmed. 4 devices, all online.
Front Door battery 85%, Backyard 92%. One motion event overnight at 03:12, front
door, no recording issues. Nothing needs action." Short, complete, sourced.

Dialogue 2, low battery: "Backyard is at 14%. Replace this weekend — cold nights
will finish it. Everything else above 60%. Want me to remind you Friday?" Actionable,
specific, with an offer attached.

Dialogue 3, offline device: "Garage Cam is offline since 22:40. Last event 22:31,
motion, recording ready. Check power and Wi-Fi; the other three are fine. Say the
word and I'll re-check." Names the outage window from real timestamps.

Dialogue 4, arming: "Arm away." — "Which panel? I see Hallway Panel and none
else." (Only one panel visible in this telling — it would just arm.) "Armed away,
panel alarm-001, 08:02. I will disarm after your test — say go." Then disarm and
confirm. Every mutating turn ends with state and restore.

Dialogue 5, incident: "Something moved at 2am." — "Three motion events 02:11–02:14,
all Driveway Cam, recordings ready. No doorbell press, no alarm events. Devices all
online now. Watch the snapshots, or say the word for live view in the browser."
Timeline first, interpretation clearly marked, next step offered.

Dialogue 6, automation: "Notify me for backyard motion at night." — Draft shown
with trigger, conditions, action, name. "Validation passed, active 24/7 in the
draft. Keep it?" User confirms or adjusts the window. Never silently deployed.

Dialogue 7, emergency: "Emergency, arm everything." — "Confirm: arming all online
panels now?" User: "Yes." — Progress per device, incident id, measures listed.
Deliberate friction, then full speed. After: disarm, confirm, log.

Dialogue 8, chat down: "Chat says no models." — "Ollama isn't answering on
127.0.0.1:11434. Start it and pull llama3.2:3b, then Refresh in Settings. Devices
and arming work fine meanwhile." Layered failure, layered answer.

Dialogue 9, no panel: "Arm the alarm." — "I see 3 devices and no alarm panel.
Cameras and doorbells can't arm. If you have a panel on MQTT, give me its id."
Refusal with reasons beats a confident hallucination every time.

Dialogue 10, history: "What happened this weekend?" — Wide history call, categorized
counts (arms, disarms, motion, alarms), busiest device, arm/disarm timeline, then
"want per-device detail or recording statuses?" Depth on demand, summary first.

## Part 18 — Glossary and index of routes

Panel, mode (home/away/disarmed/unknown), event, snapshot, stream (WebRTC only),
automation (draft), schedule (draft), incident, onboarded, mock — as defined in the
system material, repeated here so this file stands alone. Routes you will type most:
`/api/v1/health`, `/api/v1/devices`, `/api/v1/events/recent`, `/api/v1/snapshot/{id}`,
`/api/v1/devices/{id}/arm`, `/api/v1/llm/chat`, `/api/v1/llm/chat/stream`,
`/api/skills`, `/docs`. Tools you will say most: list_devices, get_security_system_status,
monitor_system_health, get_visitor_history, get_security_history, arm/disarm,
get_doorbell_status, get_camera_status. Pages you will open most: Overview, Inbox,
Doorbell, Alarms, Chat, Settings. That short list covers ninety percent of real
usage; everything else in this guide is for the remaining ten.

## Part 19 — Seasons and life events

Winter: batteries sag in the cold. After the first frost, run health and replace
anything under 30%, not 20 — the margin is the point. Snow reflects IR and can
spike motion counts; a motion-only review with a calm eye beats disabling
detection. Check mounts too: ice shifts angles, and a tilted doorbell films the
sky informatively but uselessly.

Vacation: the week before, verify arm/disarm round-trips, confirm schedules match
the trip dates, draft (don't deploy unreviewed) a wider notification automation,
designate a human who can physically respond, and leave them the disarm phrase.
During: morning rundown daily, inbox zero nightly. After: disarm, review the
full history for the absence, dismiss the backlog, then monthly-test early since
nobody was watching.

New device: claim it in the Ring app first, force-refresh inventory, confirm it
appears with the right family, run a motion test past it, check its first events
land in history, then fold it into automations and schedules by id. Rename the
device in the Ring app if the default name confuses ("Front Door" beats
"Doorbell-4F2A" in every timeline you will ever read).

Retiring a device: export its history first (history calls by device id, saved
outside the repo), remove it from automations and schedules, then release it in
the Ring app. Stale ids in drafts cause confusing not-found errors months later —
grep your saved configs, not just your memory.

Multi-site (home plus cabin, shop, parent's house): one server, one Ring account
per site keeps ids and histories clean. Cross-site questions ("everything armed?")
need one pass per server — say which site, or hear about all of them. Never merge
device lists mentally across accounts; panel ids can collide infondly similar
ways, and arming the wrong site's panel is exactly the failure this guide exists
to prevent. Label automations by site in their names.

## Part 20 — Giving feedback that gets fixed

Report confusion with the recipe: what you wanted, what you clicked or said, what
happened, what you expected, plus the health payload and the relevant log lines.
"Arm didn't work" is a mood; "arm_security_system(mode=away) returned no visible
panel with 3 devices at 08:02, health 200" is a bug report. Include versions
(dashboard Help shows them) and whether anything changed recently (upgrade, new
device, new router — the usual suspects in order).

Feature requests earn priority with a workflow attached: who, how often, what good
looks like, what you tried instead. "Support my panel" plus the device family and
a redacted device payload gets implemented; "make it better" gets admired and
shelved. Docs fixes are first-class contributions: if a paragraph here sent you
wrong, propose the corrected sentence with the tool output that proves it.

## Part 21 — Tear-out cheat sheet (the whole system on one page)

Say: "List my devices" (`list_devices`). "Morning rundown" (`get_security_system_status`
+ `monitor_system_health`). "Who visited" (`get_visitor_history`). "What happened"
(`get_security_history`). "Arm away/home" and "Disarm" (panel tools, confirmations
read back). "Test the smoke detectors" (`test_fire_safety_system`). "Cameras okay?"
(`get_camera_status`). "System healthy?" (`get_system_status`, `get_service_health`).
"Help with X" (`search_tools`, `get_tool_help`). Open: Overview for KPIs, Inbox for
events, Doorbell for snapshots and live view, Alarms for panels, Tools for the
catalog, Skills for guidance, Status for connectivity, Apps for peers, Chat for
questions, Logger for truth, Help for ports, API Docs for routes, Settings for
credentials and models. Endpoints: health, devices, events/recent, snapshot, arm,
chime, webrtc offer, llm chat (+stream), skills, capabilities, diagnostics,
shutdown. Rules that matter: confirm destructives, never invent state, unknown means
unknown, restore test arms, WebRTC only, mocks vanish on onboarding. Keep this page
open for the first month; after that you will find you no longer need it, which is
the entire point of writing it down.

Ports and env on the same page: UI 10728, API 10729, metrics 8001. Credentials
`RING_USERNAME`/`RING_PASSWORD` (or `RING_TOKEN`), LLM at `RING_LLM_BASE_URL`
(Ollama :11434 default) with `RING_LLM_MODEL` optional, MQTT under `RING_MQTT_*`
when panels hide behind the bridge. Recipes: `just dev` runs everything, `just test`
proves it, `just lint` and `just fix` keep it clean, `just bootstrap` rebuilds the
world. Logs live behind Logger and `/api/v1/logs`; truth lives behind health and
status; everything else is presentation. When stuck, re-read the health payload
first — nine times out of ten it already names the problem, the missing credential,
the offline device, or the unreached model endpoint. Print this guide's cheat
sheet, pin it near the door you leave through, and let the system earn the trust
it asks for one verified morning rundown at a time.
