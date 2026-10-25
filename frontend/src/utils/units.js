// Simple metric <-> imperial conversions for the basic-profile form.
// Height and weight are always stored/submitted in metric (cm, kg) —
// these helpers only translate what's shown to the person typing.

const CM_PER_INCH = 2.54;
const LB_PER_KG = 2.2046226218;

/** cm -> { feet, inches } (inches rounded to 1 decimal place) */
export function cmToFeetIn(cm) {
  const totalInches = cm / CM_PER_INCH;
  const feet = Math.floor(totalInches / 12);
  const inches = Math.round((totalInches - feet * 12) * 10) / 10;
  return { feet, inches };
}

/** feet + inches -> cm. Returns null if both inputs are empty. */
export function feetInToCm(feet, inches) {
  const f = feet === "" || feet == null ? null : Number(feet);
  const i = inches === "" || inches == null ? null : Number(inches);
  if (f == null && i == null) return null;
  const totalInches = (f || 0) * 12 + (i || 0);
  return totalInches * CM_PER_INCH;
}

export function kgToLbs(kg) {
  return kg * LB_PER_KG;
}

export function lbsToKg(lbs) {
  return lbs / LB_PER_KG;
}
