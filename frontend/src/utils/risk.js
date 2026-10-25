// Shared logic for turning a risk_probability into a tone (used for
// styling) and into plain-language next-step guidance. Kept in one
// place so the Results page and the final Report page never disagree
// about what counts as "high" vs "moderate" vs "low".

export function riskTone(probability) {
  if (probability == null) return "unknown";
  if (probability >= 0.6) return "high";
  if (probability >= 0.35) return "moderate";
  return "low";
}

const ACTION_GUIDANCE = {
  high: "Worth seeing a doctor in the next few weeks to follow up on this.",
  moderate: "No need to rush — mention this at your next routine visit.",
  low: "No action needed right now based on this result.",
};

export function actionGuidance(tone) {
  return ACTION_GUIDANCE[tone] || null;
}
