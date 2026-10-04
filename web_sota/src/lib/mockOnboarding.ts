/**
 * Onboarding state + declared mock content (MOCK-until-onboarded).
 *
 * Onboarded === backend health reports a valid Ring authentication.
 * Until then the Dashboard shows the red onboarding cue plus clearly badged
 * sample cards (fake actors, dashed rose borders). Mocks clear automatically
 * once configured - there is no keep-mocks toggle.
 */

export const ONBOARDED_KEY = "ring-mcp-onboarded";

export function isOnboarded(authenticationValid: boolean | undefined): boolean {
  if (authenticationValid === true) {
    try {
      localStorage.setItem(ONBOARDED_KEY, "1");
    } catch {
      /* private mode */
    }
    return true;
  }
  try {
    return (
      localStorage.getItem(ONBOARDED_KEY) === "1" &&
      authenticationValid !== false
    );
  } catch {
    return false;
  }
}

export interface MockDevice {
  id: string;
  name: string;
  type: string;
  online: boolean;
  battery: number | null;
  note: string;
}

export const MOCK_DEVICES: MockDevice[] = [
  {
    id: "mock-doorbell-1",
    name: "Joe Mocky's Front Door",
    type: "doorbell",
    online: true,
    battery: 87,
    note: "[MOCK] sample doorbell - connect Ring to see live devices",
  },
  {
    id: "mock-camera-1",
    name: "Sandra Mockinger's Backyard",
    type: "camera",
    online: false,
    battery: 12,
    note: "[MOCK] sample camera - connect Ring to see live devices",
  },
];

export const MOCK_KPIS = [
  { label: "Devices (sample)", value: "2", testid: "kpi-mock-devices" },
  { label: "Online (sample)", value: "1", testid: "kpi-mock-online" },
  { label: "Low battery (sample)", value: "1", testid: "kpi-mock-battery" },
];
