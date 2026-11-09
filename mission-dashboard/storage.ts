import type { Mission } from "./mission";

export type RecordRow = { id: string; name: string; updated: string };
type StoredRecord = RecordRow & { mission: Mission };
const storageKey = "dsop.missionDashboard.records.v1";

function records(): StoredRecord[] {
  try {
    const items = JSON.parse(localStorage.getItem(storageKey) ?? "[]");
    if (!Array.isArray(items)) throw new Error("Invalid stored records");
    return items;
  } catch {
    throw new Error("Saved missions are unavailable in this browser.");
  }
}

function write(items: StoredRecord[]) {
  try {
    localStorage.setItem(storageKey, JSON.stringify(items));
  } catch {
    throw new Error("Browser storage is full or unavailable. Download the evidence report to keep a copy.");
  }
}

function update<T>(change: () => T): Promise<T> {
  if (navigator.locks) return navigator.locks.request(storageKey, change);
  return Promise.resolve().then(change);
}

export function listMissions(): RecordRow[] {
  return records().map(({ id, name, updated }) => ({ id, name, updated })).sort((a, b) => b.updated.localeCompare(a.updated));
}

export function readMission(id: string): StoredRecord {
  const record = records().find(item => item.id === id);
  if (!record) throw new Error("The saved mission could not be found.");
  return record;
}

export function saveRecord(id: string, expected: string | null, mission: Mission): Promise<RecordRow> {
  return update(() => {
    const items = records();
    const previous = items.find(item => item.id === id);
    if ((previous?.updated ?? null) !== expected) {
      throw new Error("This record changed in another tab or was deleted. Copy your draft evidence before reopening the latest record.");
    }
    const record = { id, name: mission.name, updated: new Date().toISOString(), mission };
    write([record, ...items.filter(item => item.id !== id)]);
    return record;
  });
}

export function removeRecord(id: string): Promise<void> {
  return update(() => write(records().filter(item => item.id !== id)));
}
