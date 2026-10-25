import { useEffect, useMemo, useRef, useState } from "react";
import jsQR from "jsqr";
import ProgressSteps from "../components/ProgressSteps";
import {
  NumberField,
  SelectField,
  ChipMultiSelect,
  DualUnitNumberField,
  UnitToggle,
} from "../components/FormFields";
import { importReportQr, submitBasicProfile, ApiError } from "../api";
import { cmToFeetIn, feetInToCm, kgToLbs, lbsToKg } from "../utils/units";
import "../styles/form.css";
import "../styles/profile-page.css";

const UNIT_OPTIONS = [
  { value: "metric", label: "cm · kg" },
  { value: "imperial", label: "ft/in · lb" },
];

const SEX_OPTIONS = [
  { value: "female", label: "Female" },
  { value: "male", label: "Male" },
  { value: "intersex", label: "Intersex" },
  { value: "prefer_not_to_say", label: "Prefer not to say" },
];

const SMOKING_OPTIONS = [
  { value: "never", label: "Never smoked" },
  { value: "former", label: "Former smoker" },
  { value: "current", label: "Current smoker" },
];

const ALCOHOL_OPTIONS = [
  { value: "none", label: "None" },
  { value: "occasional", label: "Occasional" },
  { value: "moderate", label: "Moderate" },
  { value: "heavy", label: "Heavy" },
];

const ACTIVITY_OPTIONS = [
  { value: "sedentary", label: "Sedentary" },
  { value: "light", label: "Light" },
  { value: "moderate", label: "Moderate" },
  { value: "active", label: "Active" },
  { value: "very_active", label: "Very active" },
];

const FAMILY_HISTORY_OPTIONS = [
  { value: "diabetes", label: "Diabetes" },
  { value: "heart_disease", label: "Heart disease" },
  { value: "kidney_disease", label: "Kidney disease" },
  { value: "hypertension", label: "High blood pressure" },
  { value: "stroke", label: "Stroke" },
];

const EXISTING_CONDITIONS_OPTIONS = [
  { value: "hypertension", label: "High blood pressure" },
  { value: "diabetes", label: "Diabetes" },
  { value: "heart disease", label: "Heart disease" },
  { value: "coronary artery disease", label: "Coronary artery disease" },
  { value: "anemia", label: "Anemia" },
  { value: "kidney disease", label: "Kidney disease" },
];

const SYMPTOM_OPTIONS = [
  { value: "fatigue", label: "Fatigue" },
  { value: "chest_discomfort", label: "Chest discomfort" },
  { value: "shortness_of_breath", label: "Shortness of breath" },
  { value: "swelling", label: "Swelling (legs/ankles)" },
  { value: "increased_thirst", label: "Increased thirst" },
  { value: "frequent_urination", label: "Frequent urination" },
];

const initialForm = {
  age: "",
  biological_sex: "",
  height_cm: "",
  weight_kg: "",
  systolic_bp: "",
  diastolic_bp: "",
  resting_heart_rate: "",
  smoking_status: "",
  alcohol_consumption: "",
  activity_level: "",
  family_history: [],
  existing_conditions: [],
  current_symptoms: [],
};

function computeBmi(heightCm, weightKg) {
  const h = parseFloat(heightCm);
  const w = parseFloat(weightKg);
  if (!h || !w) return null;
  const meters = h / 100;
  return w / (meters * meters);
}

function bmiCategory(bmi) {
  if (bmi == null) return null;
  if (bmi < 18.5) return "underweight";
  if (bmi < 25) return "normal range";
  if (bmi < 30) return "overweight";
  return "obese range";
}

function decodeQrImage(source, canvas, maxDimension) {
  const width = source.videoWidth || source.naturalWidth;
  const height = source.videoHeight || source.naturalHeight;
  if (!width || !height) return null;
  const scale = Math.min(1, maxDimension / Math.max(width, height));
  canvas.width = Math.round(width * scale);
  canvas.height = Math.round(height * scale);
  const context = canvas.getContext("2d", { willReadFrequently: true });
  if (!context) throw new Error("Image decoding is unavailable in this browser.");
  context.drawImage(source, 0, 0, canvas.width, canvas.height);
  const imageData = context.getImageData(0, 0, canvas.width, canvas.height);
  return jsQR(imageData.data, imageData.width, imageData.height, {
    inversionAttempts: "attemptBoth",
  });
}

function validate(form, unitSystem = "metric") {
  const errors = {};

  const age = Number(form.age);
  if (!form.age) errors.age = "Age is required.";
  else if (age < 1 || age > 120) errors.age = "Enter an age between 1 and 120.";

  if (!form.biological_sex) errors.biological_sex = "Please select an option.";

  const height = Number(form.height_cm);
  if (!form.height_cm) errors.height_cm = "Height is required.";
  else if (height < 50 || height > 250)
    errors.height_cm =
      unitSystem === "imperial"
        ? "Enter a height between 1'8\" and 8'2\"."
        : "Enter a height between 50 and 250 cm.";

  const weight = Number(form.weight_kg);
  if (!form.weight_kg) errors.weight_kg = "Weight is required.";
  else if (weight < 2 || weight > 400)
    errors.weight_kg =
      unitSystem === "imperial"
        ? "Enter a weight between 4.4 and 882 lb."
        : "Enter a weight between 2 and 400 kg.";

  if (form.systolic_bp) {
    const s = Number(form.systolic_bp);
    if (s < 60 || s > 260) errors.systolic_bp = "Enter a value between 60 and 260 mmHg.";
  }
  if (form.diastolic_bp) {
    const d = Number(form.diastolic_bp);
    if (d < 30 || d > 180) errors.diastolic_bp = "Enter a value between 30 and 180 mmHg.";
  }
  if (form.systolic_bp && form.diastolic_bp) {
    if (Number(form.diastolic_bp) >= Number(form.systolic_bp)) {
      errors.diastolic_bp = "Diastolic must be lower than systolic.";
    }
  }
  if (form.resting_heart_rate) {
    const hr = Number(form.resting_heart_rate);
    if (hr < 25 || hr > 220) errors.resting_heart_rate = "Enter a value between 25 and 220 bpm.";
  }

  if (!form.smoking_status) errors.smoking_status = "Please select an option.";
  if (!form.alcohol_consumption) errors.alcohol_consumption = "Please select an option.";
  if (!form.activity_level) errors.activity_level = "Please select an option.";

  const bmi = computeBmi(form.height_cm, form.weight_kg);
  if (bmi && (bmi < 8 || bmi > 60)) {
    errors.weight_kg =
      "This height/weight combination gives an implausible BMI — please double-check the values.";
  }

  return errors;
}

export default function BasicProfile({ onBackToHome, onSubmitted }) {
  const [form, setForm] = useState(initialForm);
  const [unitSystem, setUnitSystem] = useState("metric");
  const [errors, setErrors] = useState({});
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState(null);
  const [scanOpen, setScanOpen] = useState(false);
  const [scanText, setScanText] = useState("");
  const [scanError, setScanError] = useState(null);
  const [scanStatus, setScanStatus] = useState(null);
  const [pendingImport, setPendingImport] = useState(null);
  const [importedMeasurements, setImportedMeasurements] = useState({});
  const videoRef = useRef(null);
  const streamRef = useRef(null);
  const scanFrameRef = useRef(null);
  const imageInputRef = useRef(null);
  const captureInputRef = useRef(null);
  const scannerAttemptRef = useRef(0);

  const bmi = useMemo(
    () => computeBmi(form.height_cm, form.weight_kg),
    [form.height_cm, form.weight_kg]
  );
  const imperialHeight = cmToFeetIn(Number(form.height_cm) || 0);

  const setField = (key) => (value) => setForm((f) => ({ ...f, [key]: value }));
  const setImperialHeight = (feet, inches) => {
    const height = feetInToCm(feet, inches);
    setField("height_cm")(height == null || !Number.isFinite(height) ? "" : height);
  };

  const stopScanner = () => {
    scannerAttemptRef.current += 1;
    if (scanFrameRef.current != null) {
      window.clearTimeout(scanFrameRef.current);
      scanFrameRef.current = null;
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    if (videoRef.current) videoRef.current.srcObject = null;
    setScanOpen(false);
  };

  useEffect(() => () => stopScanner(), []);

  const requestReportImport = async (payload) => {
    setScanError(null);
    setScanStatus("Checking report data…");
    try {
      const imported = await importReportQr(payload);
      setPendingImport(imported);
      setScanStatus("Review the imported values below before using them.");
    } catch (err) {
      setScanError(err instanceof ApiError ? err.message : "Could not read this report.");
      setScanStatus(null);
    }
  };

  const startScanner = async () => {
    if (scanOpen || streamRef.current) return;
    const attempt = scannerAttemptRef.current + 1;
    scannerAttemptRef.current = attempt;
    setScanError(null);
    setScanStatus("Starting camera…");
    if (window.isSecureContext === false) {
      setScanError("Camera access requires a secure connection (HTTPS) or localhost. You can upload a QR image instead.");
      setScanStatus(null);
      return;
    }
    if (!navigator.mediaDevices?.getUserMedia) {
      setScanError("Camera access is not available in this browser. Upload a QR image or paste the QR data instead.");
      setScanStatus(null);
      return;
    }
    setScanOpen(true);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: { ideal: "environment" } },
      });
      if (scannerAttemptRef.current !== attempt) {
        stream.getTracks().forEach((track) => track.stop());
        return;
      }
      streamRef.current = stream;
      const video = videoRef.current;
      if (!video) throw new Error("Camera preview is unavailable.");
      video.srcObject = stream;
      await video.play();
      if (scannerAttemptRef.current !== attempt) return;
      setScanStatus("Point the camera at the QR code.");
      const canvas = document.createElement("canvas");
      const scanFrame = () => {
        if (!videoRef.current || streamRef.current !== stream) return;
        try {
          const code = decodeQrImage(video, canvas, 1600);
          if (code?.data) {
            stopScanner();
            requestReportImport(code.data);
            return;
          }
        } catch (err) {
          stopScanner();
          setScanError(err instanceof Error ? err.message : "Could not read the camera image.");
          setScanStatus(null);
          return;
        }
        scanFrameRef.current = window.setTimeout(scanFrame, 120);
      };
      scanFrameRef.current = window.setTimeout(scanFrame, 120);
    } catch (err) {
      stopScanner();
      if (err?.name === "NotAllowedError" || err?.name === "SecurityError") {
        setScanError("Camera permission was denied. Allow camera access in your browser settings, or upload a QR image instead.");
      } else if (err?.name === "NotFoundError" || err?.name === "OverconstrainedError") {
        setScanError("No usable camera was found. Upload a QR image or paste the QR data instead.");
      } else if (err?.name === "NotReadableError") {
        setScanError("The camera is already in use by another app. Close it or upload a QR image instead.");
      } else {
        setScanError(err instanceof Error ? err.message : "Camera access was unavailable. Upload a QR image or paste the QR data instead.");
      }
      setScanStatus(null);
    }
  };

  const handleImageSelected = async (event) => {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;
    if (file.type && !file.type.startsWith("image/")) {
      setScanError("Choose an image file containing a QR code.");
      setScanStatus(null);
      return;
    }
    if (file.size > 15 * 1024 * 1024) {
      setScanError("Choose an image smaller than 15 MB.");
      setScanStatus(null);
      return;
    }

    stopScanner();
    setScanError(null);
    setScanStatus("Reading the image on this device…");
    const imageUrl = URL.createObjectURL(file);
    try {
      const image = new Image();
      await new Promise((resolve, reject) => {
        image.onload = resolve;
        image.onerror = () => reject(new Error("Could not open this image."));
        image.src = imageUrl;
      });
      const canvas = document.createElement("canvas");
      const code = decodeQrImage(image, canvas, 2048);
      if (!code?.data) {
        throw new Error("No QR code was found in that image. Try a clearer, well-lit photo.");
      }
      await requestReportImport(code.data);
    } catch (err) {
      setScanError(err instanceof Error ? err.message : "Could not read a QR code from this image.");
      setScanStatus(null);
    } finally {
      URL.revokeObjectURL(imageUrl);
    }
  };

  const confirmImport = () => {
    const imported = pendingImport.basic_profile || {};
    setForm((current) => ({
      ...current,
      ...imported,
      family_history: imported.family_history ?? current.family_history,
      existing_conditions: imported.existing_conditions ?? current.existing_conditions,
      current_symptoms: imported.current_symptoms ?? current.current_symptoms,
    }));
    setImportedMeasurements(pendingImport.followup_answers || {});
    setPendingImport(null);
    setScanStatus("Report values added. Review them before continuing.");
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const validationErrors = validate(form, unitSystem);
    setErrors(validationErrors);
    if (Object.keys(validationErrors).length > 0) {
      const firstErrorField = document.getElementById(Object.keys(validationErrors)[0]);
      firstErrorField?.scrollIntoView({ behavior: "smooth", block: "center" });
      return;
    }

    const payload = {
      age: Number(form.age),
      biological_sex: form.biological_sex,
      height_cm: Number(form.height_cm),
      weight_kg: Number(form.weight_kg),
      systolic_bp: form.systolic_bp ? Number(form.systolic_bp) : null,
      diastolic_bp: form.diastolic_bp ? Number(form.diastolic_bp) : null,
      resting_heart_rate: form.resting_heart_rate ? Number(form.resting_heart_rate) : null,
      smoking_status: form.smoking_status,
      alcohol_consumption: form.alcohol_consumption,
      activity_level: form.activity_level,
      family_history: form.family_history,
      existing_conditions: form.existing_conditions,
      current_symptoms: form.current_symptoms,
      report_measurements: importedMeasurements,
    };

    setSubmitting(true);
    setSubmitError(null);
    try {
      const result = await submitBasicProfile(payload);
      onSubmitted(result);
    } catch (err) {
      setSubmitError(
        err instanceof ApiError
          ? err.message
          : "Could not reach the screening service. Check that the backend is running and try again."
      );
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="profile-page">
      <div className="profile-page-inner">
        <ProgressSteps currentIndex={0} />
        <h1 className="profile-title">Basic health profile</h1>
        <p className="profile-intro">
          This general information is shared across every condition the
          system screens for. It takes about two minutes.
        </p>

        <section className="report-import" aria-labelledby="report-import-title">
          <div>
            <h2 id="report-import-title" className="form-section-title">Have a medical report?</h2>
            <p className="form-section-desc">
              Scan a QR code containing structured report data, review what was found,
              then add the confirmed values to this screening.
            </p>
          </div>
          <div className="report-import-actions">
            <button type="button" className="btn-primary" onClick={startScanner} disabled={scanOpen}>
              Use camera
            </button>
            <button
              type="button"
              className="btn-secondary"
              onClick={() => imageInputRef.current?.click()}
            >
              Choose image / Drive file
            </button>
            <button
              type="button"
              className="btn-secondary report-capture-button"
              onClick={() => captureInputRef.current?.click()}
            >
              Take a photo
            </button>
            <input
              ref={imageInputRef}
              className="report-image-input"
              type="file"
              accept="image/*"
              aria-label="Choose an image containing a QR code"
              onChange={handleImageSelected}
            />
            <input
              ref={captureInputRef}
              className="report-image-input"
              type="file"
              accept="image/*"
              capture="environment"
              aria-label="Take a photo of a QR code"
              onChange={handleImageSelected}
            />
          </div>
          <p className="field-hint">
            Choose an image from your device or an available cloud-drive location, or take a new photo on mobile. Images are decoded on your device.
          </p>

          {scanOpen && (
            <div className="report-scanner">
              <video ref={videoRef} className="report-scanner-video" muted playsInline />
              <button type="button" className="btn-secondary" onClick={() => {
                stopScanner();
                setScanStatus(null);
              }}>
                Stop camera
              </button>
            </div>
          )}

          <div className="report-paste">
            <label className="field-label" htmlFor="qr-payload">Or paste QR data</label>
            <textarea
              id="qr-payload"
              className="report-paste-input"
              value={scanText}
              onChange={(event) => setScanText(event.target.value)}
              placeholder='{"age": 52, "biological_sex": "female", "glucose": 110}'
              rows={3}
            />
            <button
              type="button"
              className="btn-secondary"
              onClick={() => requestReportImport(scanText)}
              disabled={!scanText.trim()}
            >
              Check pasted data
            </button>
          </div>

          {scanStatus && <p className="field-hint" role="status" aria-live="polite">{scanStatus}</p>}
          {scanError && <p className="field-error" role="alert">{scanError}</p>}

          {pendingImport && (
            <div className="report-import-preview">
              <h3>Review imported values</h3>
              <ul>
                {[...Object.entries(pendingImport.basic_profile), ...Object.entries(pendingImport.followup_answers)].map(([key, value]) => (
                  <li key={key}><strong>{key.replaceAll("_", " ")}</strong>: {String(value)}</li>
                ))}
              </ul>
              <p className="field-hint">Names and patient identifiers are ignored.</p>
              <div className="report-import-actions">
                <button type="button" className="btn-secondary" onClick={() => setPendingImport(null)}>Discard</button>
                <button type="button" className="btn-primary" onClick={confirmImport}>Use imported data</button>
              </div>
            </div>
          )}
        </section>

        <form onSubmit={handleSubmit} noValidate>
          <section className="form-section">
            <h2 className="form-section-title">Demographics</h2>
            <div className="field-grid">
              <NumberField
                id="age"
                label="Age"
                unit="years"
                value={form.age}
                onChange={setField("age")}
                min={1}
                max={120}
                error={errors.age}
              />
              <SelectField
                id="biological_sex"
                label="Biological sex"
                value={form.biological_sex}
                onChange={setField("biological_sex")}
                options={SEX_OPTIONS}
                error={errors.biological_sex}
                hint="Used because it affects reference ranges for several measurements."
              />
            </div>
          </section>

          <section className="form-section">
            <h2 className="form-section-title">Body measurements</h2>
            <UnitToggle
              id="measurement-units"
              value={unitSystem}
              onChange={setUnitSystem}
              options={UNIT_OPTIONS}
            />
            <div className="field-grid">
              {unitSystem === "metric" ? (
                <>
                  <NumberField
                    id="height_cm"
                    label="Height"
                    unit="cm"
                    value={form.height_cm}
                    onChange={setField("height_cm")}
                    min={50}
                    max={250}
                    error={errors.height_cm}
                  />
                  <NumberField
                    id="weight_kg"
                    label="Weight"
                    unit="kg"
                    value={form.weight_kg}
                    onChange={setField("weight_kg")}
                    min={2}
                    max={400}
                    step={0.1}
                    error={errors.weight_kg}
                  />
                </>
              ) : (
                <>
                  <DualUnitNumberField
                    htmlFor="height_feet"
                    label="Height"
                    valueA={form.height_cm ? imperialHeight.feet : ""}
                    onChangeA={(feet) => setImperialHeight(feet, imperialHeight.inches)}
                    unitA="ft"
                    minA={0}
                    maxA={8}
                    valueB={form.height_cm ? imperialHeight.inches : ""}
                    onChangeB={(inches) => setImperialHeight(imperialHeight.feet, inches)}
                    unitB="in"
                    minB={0}
                    maxB={11.9}
                    error={errors.height_cm}
                  />
                  <NumberField
                    id="weight_kg"
                    label="Weight"
                    unit="lb"
                    value={form.weight_kg ? (kgToLbs(Number(form.weight_kg))).toFixed(1) : ""}
                    onChange={(pounds) => {
                      const kilograms = pounds === "" ? "" : lbsToKg(Number(pounds));
                      setField("weight_kg")(Number.isFinite(kilograms) ? kilograms : "");
                    }}
                    min={4.4}
                    max={882}
                    step={0.1}
                    error={errors.weight_kg}
                  />
                </>
              )}
            </div>
            {bmi && !errors.weight_kg && (
              <div className="bmi-readout">
                <span className="bmi-readout-value">{bmi.toFixed(1)}</span>
                <span className="bmi-readout-label">
                  calculated BMI · {bmiCategory(bmi)}
                </span>
              </div>
            )}
          </section>

          <section className="form-section">
            <h2 className="form-section-title">Vitals</h2>
            <p className="form-section-desc">
              Optional — leave blank if you don't have a recent reading.
              These improve the initial screening but aren't required.
            </p>
            <div className="field-grid">
              <NumberField
                id="systolic_bp"
                label="Systolic blood pressure"
                unit="mmHg"
                value={form.systolic_bp}
                onChange={setField("systolic_bp")}
                min={60}
                max={260}
                error={errors.systolic_bp}
                hint="The higher (top) number on a blood pressure reading."
              />
              <NumberField
                id="diastolic_bp"
                label="Diastolic blood pressure"
                unit="mmHg"
                value={form.diastolic_bp}
                onChange={setField("diastolic_bp")}
                min={30}
                max={180}
                error={errors.diastolic_bp}
                hint="The lower (bottom) number on a blood pressure reading."
              />
            </div>
            <NumberField
              id="resting_heart_rate"
              label="Resting heart rate"
              unit="bpm"
              value={form.resting_heart_rate}
              onChange={setField("resting_heart_rate")}
              min={25}
              max={220}
              error={errors.resting_heart_rate}
              hint="Your pulse while sitting calmly — most fitness trackers and smartwatches show this."
            />
          </section>

          <section className="form-section">
            <h2 className="form-section-title">Lifestyle</h2>
            <div className="field-grid">
              <SelectField
                id="smoking_status"
                label="Smoking status"
                value={form.smoking_status}
                onChange={setField("smoking_status")}
                options={SMOKING_OPTIONS}
                error={errors.smoking_status}
              />
              <SelectField
                id="alcohol_consumption"
                label="Alcohol consumption"
                value={form.alcohol_consumption}
                onChange={setField("alcohol_consumption")}
                options={ALCOHOL_OPTIONS}
                error={errors.alcohol_consumption}
              />
            </div>
            <SelectField
              id="activity_level"
              label="Physical activity level"
              value={form.activity_level}
              onChange={setField("activity_level")}
              options={ACTIVITY_OPTIONS}
              error={errors.activity_level}
            />
          </section>

          <section className="form-section">
            <h2 className="form-section-title">History &amp; symptoms</h2>
            <p className="form-section-desc">
              Optional. Select anything that applies — these help decide
              which follow-up questions to ask next.
            </p>
            <ChipMultiSelect
              label="Family history"
              values={form.family_history}
              onChange={setField("family_history")}
              options={FAMILY_HISTORY_OPTIONS}
            />
            <ChipMultiSelect
              label="Existing conditions you've been diagnosed with"
              values={form.existing_conditions}
              onChange={setField("existing_conditions")}
              options={EXISTING_CONDITIONS_OPTIONS}
            />
            <ChipMultiSelect
              label="Current symptoms"
              values={form.current_symptoms}
              onChange={setField("current_symptoms")}
              options={SYMPTOM_OPTIONS}
            />
          </section>

          {submitError && <p className="form-submit-error">{submitError}</p>}

          <div className="form-actions">
            <button type="button" className="btn-secondary" onClick={onBackToHome}>
              ← Home
            </button>
            <p className="form-actions-note">
              Nothing here is stored beyond this session.
            </p>
            <button className="btn-primary" type="submit" disabled={submitting}>
              {submitting ? "Submitting…" : "Continue to screening"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
