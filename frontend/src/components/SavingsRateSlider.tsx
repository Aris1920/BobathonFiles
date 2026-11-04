const fmt = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
  maximumFractionDigits: 0,
});

interface SavingsRateSliderProps {
  value: number;
  onChange: (val: number) => void;
  monthlyTakeHome: number;
}

export default function SavingsRateSlider({ value, onChange, monthlyTakeHome }: SavingsRateSliderProps) {
  const monthlyPayment = monthlyTakeHome * (value / 100);

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-1 mb-3">
        <label htmlFor="savings-rate-slider" className="text-sm font-semibold text-gray-700">
          Savings Rate
        </label>
        <span className="text-sm text-gray-500">
          Saving{' '}
          <span className="font-bold text-gray-800">{value}%</span>{' '}
          of take-home pay ≈{' '}
          <span className="font-bold text-gray-800">{fmt.format(monthlyPayment)}/mo</span>
        </span>
      </div>

      <input
        id="savings-rate-slider"
        type="range"
        min={5}
        max={50}
        step={1}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full accent-blue-600 cursor-pointer"
      />

      <div className="flex justify-between text-xs text-gray-400 mt-1">
        <span>5%</span>
        <span>50%</span>
      </div>
    </div>
  );
}
