import { useId } from "react";

/**
 * 1-5 yıldız seçimi. Altta radyo düğmeleri var: klavyeyle ok tuşları çalışır, ekran okuyucu "3 / 5 yıldız" okur.
 */
export function StarRating({
  value,
  onChange,
  legend,
  disabled,
}: {
  value: number | undefined;
  onChange: (value: number) => void;
  legend: string;
  disabled?: boolean;
}) {
  const name = useId();
  return (
    <fieldset className="stars" disabled={disabled}>
      <legend className="stars__legend">{legend}</legend>
      <div className="stars__row">
        {[1, 2, 3, 4, 5].map((n) => (
          <label key={n} className={value !== undefined && n <= value ? "stars__star stars__star--on" : "stars__star"}>
            <input
              type="radio"
              name={name}
              value={n}
              checked={value === n}
              onChange={() => onChange(n)}
              className="visually-hidden"
            />
            <span aria-hidden="true">★</span>
            <span className="visually-hidden">{n} / 5 yıldız</span>
          </label>
        ))}
      </div>
    </fieldset>
  );
}
