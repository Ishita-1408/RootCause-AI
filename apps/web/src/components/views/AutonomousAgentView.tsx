import React from 'react';
import { AutonomousAgentPanel } from '../AutonomousAgentPanel';
import { InvestigationAgentResponse } from '../../types/api';

interface AutonomousAgentViewProps {
  data: InvestigationAgentResponse | null;
  isLoading: boolean;
  selectedDate: string;
}

export const AutonomousAgentView: React.FC<AutonomousAgentViewProps> = (props) => {
  return (
    <div className="space-y-6">
      <AutonomousAgentPanel {...props} />
    </div>
  );
};
