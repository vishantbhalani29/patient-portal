/**
 * Utility functions for converting and formatting datetimes between UTC (Backend)
 * and Indian Standard Time (IST, Asia/Kolkata - UTC+5:30) for the UI.
 */

/**
 * Safely parses an ISO datetime string as UTC.
 * If the string lacks a trailing 'Z' or timezone offset (+HH:MM / -HH:MM),
 * appends 'Z' so JavaScript Date constructor treats it as UTC rather than naive local time.
 */
export function parseUtc(utcString: string): Date {
  if (!utcString) return new Date(NaN);

  let normalized = utcString.trim();
  const hasTimezone = /[Zz]|\+\d{2}:?\d{2}|-\d{2}:?\d{2}$/.test(normalized);

  if (!hasTimezone) {
    normalized += 'Z';
  }

  return new Date(normalized);
}

// Internal helper to extract date/time components in Asia/Kolkata timezone
function getIstParts(date: Date) {
  const formatter = new Intl.DateTimeFormat('en-US', {
    timeZone: 'Asia/Kolkata',
    year: 'numeric',
    month: 'numeric',
    day: 'numeric',
    hour: 'numeric',
    minute: 'numeric',
    second: 'numeric',
    hour12: false,
  });

  const parts = formatter.formatToParts(date);
  const getPart = (type: string) =>
    parseInt(parts.find((p) => p.type === type)?.value || '0', 10);

  return {
    year: getPart('year'),
    month: getPart('month'), // 1-12
    day: getPart('day'),
    hour: getPart('hour') % 24, // 0-23
    minute: getPart('minute'),
    second: getPart('second'),
  };
}

/**
 * 1. Formats a UTC ISO timestamp into a human-readable IST string.
 * Uses parseUtc() to guarantee naive ISO strings (without Z) are treated as UTC.
 * Example: "2026-09-01T04:40:00" -> "1 Sep 2026 • 10:10 AM IST"
 */
export function formatUtcToIST(utcString?: string | null): string {
  if (!utcString) return 'Not scheduled';

  const date = parseUtc(utcString);
  if (isNaN(date.getTime())) return 'Invalid date';

  const dateFormatted = new Intl.DateTimeFormat('en-IN', {
    timeZone: 'Asia/Kolkata',
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  }).format(date);

  const timeFormatted = new Intl.DateTimeFormat('en-IN', {
    timeZone: 'Asia/Kolkata',
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
  }).format(date);

  return `${dateFormatted} • ${timeFormatted} IST`;
}

/**
 * 2. Converts a UTC ISO timestamp string into a YYYY-MM-DDTHH:mm string in IST timezone.
 * Uses parseUtc() to guarantee naive ISO strings (without Z) are treated as UTC.
 * Used for populating datetime-local input fields in IST.
 * Example: "2026-09-01T04:40:00" -> "2026-09-01T10:10"
 */
export function utcToDatetimeLocal(utcString?: string | null): string {
  if (!utcString) return '';

  const date = parseUtc(utcString);
  if (isNaN(date.getTime())) return '';

  const { year, month, day, hour, minute } = getIstParts(date);

  const pad = (n: number) => n.toString().padStart(2, '0');
  return `${year}-${pad(month)}-${pad(day)}T${pad(hour)}:${pad(minute)}`;
}

/**
 * 3. Converts an IST datetime-local input string (e.g. "2026-09-01T10:10")
 * into an ISO UTC string (e.g. "2026-09-01T04:40:00.000Z").
 * Used when submitting form payloads to the API.
 */
export function datetimeLocalToUtc(localValue: string): string {
  if (!localValue) return '';

  const [datePart, timePart] = localValue.split('T');
  if (!datePart || !timePart) return '';

  const [yearStr, monthStr, dayStr] = datePart.split('-');
  const [hourStr, minuteStr] = timePart.split(':');

  const year = parseInt(yearStr, 10);
  const month = parseInt(monthStr, 10) - 1; // 0-indexed in JS Date
  const day = parseInt(dayStr, 10);
  const hour = parseInt(hourStr, 10);
  const minute = parseInt(minuteStr, 10);

  // IST is UTC + 05:30. Subtract 5 hours and 30 minutes to derive UTC.
  const utcDate = new Date(Date.UTC(year, month, day, hour - 5, minute - 30, 0, 0));

  return utcDate.toISOString();
}
