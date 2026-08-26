import React from 'react';
import { AnomalyTimeline } from '../AnomalyTimeline';
import { AnomalyDetectionResponse, MetricType } from '../../types/api';
import { NavSection } from '../Sidebar';

interface AnomaliesViewProps {
  data: AnomalyDetectionResponse | null;
  selectedDate: string;
  onSelectDate: (date: string) => void;
  onNavigate?: (section: NavSection) => void;
  metric: MetricType;
  isLoading: boolean;
}

export const AnomaliesView: React.FC<AnomaliesViewProps> = ({
  data,
  selectedDate,
  onSelectDate,
  onNavigate,
  metric,
  isLoading,
}) => {
  return (
    <div className="space-y-6">
      <AnomalyTimeline
        data={data}
        selectedDate={selectedDate}
        onSelectDate={onSelectDate}
        metric={metric}
        isLoading={isLoading}
        onNavigateToRootCause={onNavigate ? () => onNavigate('root-cause') : undefined}
      />
    </div>
  );
};
