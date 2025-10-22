import { FileJson, FileText } from 'lucide-react';
import type { AnalysisResult, Listing } from '../types';

interface AnalysisResultsProps {
  results: AnalysisResult[];
  listings: Listing[];
}

export function AnalysisResults({ results, listings }: AnalysisResultsProps) {
  const getListingById = (id: string) => listings.find((l) => l.id === id);

  const downloadJSON = (result: AnalysisResult) => {
    const blob = new Blob([JSON.stringify(result.rawJson, null, 2)], {
      type: 'application/json',
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `analysis-${result.listingId}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const downloadMarkdown = (result: AnalysisResult) => {
    const listing = getListingById(result.listingId);
    const markdown = `# Analysis Report: ${listing?.address || result.listingId}

## Property Details
- **Address**: ${listing?.address || 'N/A'}
- **Price**: $${listing?.price ? listing.price.toLocaleString() : 'N/A'}
- **Cap Rate**: ${listing?.capRate ?? 'N/A'}%
- **Units**: ${listing?.units ?? 'N/A'}
- **Size**: ${listing?.size ? listing.size.toLocaleString() : 'N/A'} sqft

## Agent Analysis

${result.agents.map((agent) => `### ${agent.name}
**Score**: ${agent.score}/100
${agent.summary}
`).join('\n')}

## Final Summary

**Overall Score**: ${result.final.overallScore}/100

${result.final.summary}

---
*Generated on ${new Date().toLocaleDateString()}*
`;

    const blob = new Blob([markdown], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `analysis-${result.listingId}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  if (results.length === 0) {
    return null;
  }

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-900">Analysis Results</h2>

      {results.map((result) => {
        const listing = getListingById(result.listingId);
        return (
          <div key={result.listingId} className="bg-white rounded-lg shadow p-6 space-y-4">
            <div className="flex items-start justify-between">
              <div>
                <h3 className="text-xl font-semibold text-gray-900">
                  {listing?.address || `Listing ${result.listingId}`}
                </h3>
                {listing && (
                  <p className="text-sm text-gray-600 mt-1">
                    {listing.price ? `$${(listing.price / 1_000_000).toFixed(2)}M` : 'N/A'} • {listing.capRate ?? 'N/A'}% Cap Rate
                  </p>
                )}
              </div>
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => downloadJSON(result)}
                  className="flex items-center space-x-1 px-3 py-2 text-sm bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-md transition-colors"
                  title="Download JSON"
                >
                  <FileJson className="w-4 h-4" />
                  <span>JSON</span>
                </button>
                <button
                  onClick={() => downloadMarkdown(result)}
                  className="flex items-center space-x-1 px-3 py-2 text-sm bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-md transition-colors"
                  title="Download Markdown"
                >
                  <FileText className="w-4 h-4" />
                  <span>MD</span>
                </button>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {result.agents.map((agent) => (
                <div
                  key={agent.name}
                  className="border border-gray-200 rounded-md p-4 space-y-2"
                >
                  <div className="flex items-center justify-between">
                    <h4 className="font-semibold text-gray-900">{agent.name}</h4>
                    <span
                      className={`px-2 py-1 text-xs font-bold rounded ${
                        agent.score >= 80
                          ? 'bg-green-100 text-green-800'
                          : agent.score >= 60
                          ? 'bg-yellow-100 text-yellow-800'
                          : 'bg-red-100 text-red-800'
                      }`}
                    >
                      {agent.score}
                    </span>
                  </div>
                  <p className="text-sm text-gray-600">{agent.summary}</p>
                </div>
              ))}
            </div>

            <div className="border-t border-gray-200 pt-4 mt-4">
              <div className="flex items-center justify-between mb-3">
                <h4 className="text-lg font-semibold text-gray-900">Final Summary</h4>
                <span
                  className={`px-3 py-1 text-sm font-bold rounded ${
                    result.final.overallScore >= 80
                      ? 'bg-green-100 text-green-800'
                      : result.final.overallScore >= 60
                      ? 'bg-yellow-100 text-yellow-800'
                      : 'bg-red-100 text-red-800'
                  }`}
                >
                  Overall: {result.final.overallScore}
                </span>
              </div>
              <p className="text-gray-700">{result.final.summary}</p>
            </div>
          </div>
        );
      })}
    </div>
  );
}
