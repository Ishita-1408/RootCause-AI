import React from 'react';
import { AIMemoPanel } from '../AIMemoPanel';
import { AIInvestigationResponse } from '../../types/api';

interface AIMemoViewProps {
  data: AIInvestigationResponse | null;
  isLoading: boolean;
}

export const AIMemoView: React.FC<AIMemoViewProps> = (props) => {
  return (
    <div className="space-y-6">
      <AIMemoPanel {...props} />
    </div>
  );
};
