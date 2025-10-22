import { Loader2 } from 'lucide-react';

interface AgentChooserProps {
  selectedCrews: string[];
  onCrewsChange: (crews: string[]) => void;
  onAnalyze: () => void;
  canAnalyze: boolean;
  loading: boolean;
}

const AVAILABLE_CREWS: { key: string; label: string }[] = [
  { key: 'investment', label: 'Investment' },
  { key: 'location', label: 'Location Risk' },
  { key: 'news', label: 'News / Reddit' },
  { key: 'vc_risk', label: 'VC Risk / Return' },
  { key: 'construction', label: 'Construction' },
  { key: 'la_city', label: 'LA City Data' },
];

export function AgentChooser({
  selectedCrews,
  onCrewsChange,
  onAnalyze,
  canAnalyze,
  loading,
}: AgentChooserProps) {
  const toggleCrew = (crewKey: string) => {
    if (selectedCrews.includes(crewKey)) {
      onCrewsChange(selectedCrews.filter((c) => c !== crewKey));
    } else {
      onCrewsChange([...selectedCrews, crewKey]);
    }
  };

  const toggleAll = () => {
    if (selectedCrews.length === AVAILABLE_CREWS.length) {
      onCrewsChange([]);
    } else {
      onCrewsChange(AVAILABLE_CREWS.map((crew) => crew.key));
    }
  };

  return (
    <div className="bg-white rounded-lg shadow p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-gray-900">Select Analysis Crews</h2>
        <button
          onClick={toggleAll}
          className="text-sm text-blue-600 hover:text-blue-700 font-medium"
        >
          {selectedCrews.length === AVAILABLE_CREWS.length ? 'Deselect All' : 'Select All'}
        </button>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
        {AVAILABLE_CREWS.map((crew) => (
          <label
            key={crew.key}
            className="flex items-center space-x-2 p-3 border border-gray-200 rounded-md hover:bg-gray-50 cursor-pointer"
          >
            <input
              type="checkbox"
              checked={selectedCrews.includes(crew.key)}
              onChange={() => toggleCrew(crew.key)}
              className="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
            />
            <span className="text-sm font-medium text-gray-700">{crew.label}</span>
          </label>
        ))}
      </div>

      <button
        onClick={onAnalyze}
        disabled={!canAnalyze || loading}
        className="w-full bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white font-medium py-3 px-6 rounded-md transition-colors flex items-center justify-center"
      >
        {loading ? (
          <>
            <Loader2 className="w-5 h-5 mr-2 animate-spin" />
            Analyzing...
          </>
        ) : (
          'Run Analysis'
        )}
      </button>

      {!canAnalyze && !loading && (
        <p className="text-sm text-gray-600 text-center">
          Select at least one listing and one crew to run analysis
        </p>
      )}
    </div>
  );
}
