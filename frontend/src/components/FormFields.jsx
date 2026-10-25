import "../styles/form.css";

export function FieldWrap({ label, htmlFor, error, hint, children }) {
  return (
    <div className={`field-wrap${error ? " field-wrap--error" : ""}`}>
      <label htmlFor={htmlFor} className="field-label">
        {label}
      </label>
      {children}
      {hint && !error && <p className="field-hint">{hint}</p>}
      {error && (
        <p className="field-error" role="alert">
          {error}
        </p>
      )}
    </div>
  );
}

export function NumberField({
  id,
  label,
  value,
  onChange,
  min,
  max,
  step = 1,
  unit,
  error,
  hint,
}) {
  return (
    <FieldWrap label={label} htmlFor={id} error={error} hint={hint}>
      <div className="input-with-unit">
        <input
          id={id}
          type="number"
          inputMode="decimal"
          value={value}
          min={min}
          max={max}
          step={step}
          onChange={(e) => onChange(e.target.value)}
          className="text-input"
        />
        {unit && <span className="input-unit">{unit}</span>}
      </div>
    </FieldWrap>
  );
}

export function DualUnitNumberField({
  label,
  htmlFor,
  error,
  hint,
  valueA,
  onChangeA,
  unitA,
  minA,
  maxA,
  valueB,
  onChangeB,
  unitB,
  minB,
  maxB,
  stepB = 0.1,
}) {
  return (
    <FieldWrap label={label} htmlFor={htmlFor} error={error} hint={hint}>
      <div className="dual-input-row">
        <div className="input-with-unit">
          <input
            id={htmlFor}
            type="number"
            inputMode="decimal"
            value={valueA}
            min={minA}
            max={maxA}
            onChange={(e) => onChangeA(e.target.value)}
            className="text-input"
          />
          {unitA && <span className="input-unit">{unitA}</span>}
        </div>
        <div className="input-with-unit">
          <input
            id={`${htmlFor}_secondary`}
            type="number"
            inputMode="decimal"
            value={valueB}
            min={minB}
            max={maxB}
            step={stepB}
            onChange={(e) => onChangeB(e.target.value)}
            className="text-input"
          />
          {unitB && <span className="input-unit">{unitB}</span>}
        </div>
      </div>
    </FieldWrap>
  );
}

export function UnitToggle({ id, value, onChange, options }) {
  return (
    <div className="unit-toggle" role="group" aria-label="Units">
      {options.map((opt) => (
        <button
          key={opt.value}
          type="button"
          className={`unit-toggle-btn${value === opt.value ? " unit-toggle-btn--active" : ""}`}
          aria-pressed={value === opt.value}
          onClick={() => onChange(opt.value)}
        >
          {opt.label}
        </button>
      ))}
    </div>
  );
}

export function SelectField({ id, label, value, onChange, options, error, hint }) {
  return (
    <FieldWrap label={label} htmlFor={id} error={error} hint={hint}>
      <select
        id={id}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="select-input"
      >
        <option value="" disabled>
          Select…
        </option>
        {options.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
    </FieldWrap>
  );
}

export function ChipMultiSelect({ label, values, onChange, options, hint }) {
  const toggle = (val) => {
    if (values.includes(val)) {
      onChange(values.filter((v) => v !== val));
    } else {
      onChange([...values, val]);
    }
  };
  return (
    <div className="field-wrap">
      <span className="field-label">{label}</span>
      <div className="chip-row">
        {options.map((opt) => {
          const active = values.includes(opt.value);
          return (
            <button
              type="button"
              key={opt.value}
              className={`chip${active ? " chip--active" : ""}`}
              aria-pressed={active}
              onClick={() => toggle(opt.value)}
            >
              {opt.label}
            </button>
          );
        })}
      </div>
      {hint && <p className="field-hint">{hint}</p>}
    </div>
  );
}
