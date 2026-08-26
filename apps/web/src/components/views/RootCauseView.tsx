import React from 'react';
import { RootCausePanel } from '../RootCausePanel';
import { RootCauseInvestigationResponse } from '../../types/api';

interface RootCauseViewProps {
  data: RootCauseInvestigationResponse | null;
  isLoading: boolean;
  selectedDate: string;
}

export const RootCauseView: React.FC<RootCauseViewProps> = (props) => {
  return (
    <div className="space-y-6">
      <RootCausePanel {...props} />
    </div>
  );
};
