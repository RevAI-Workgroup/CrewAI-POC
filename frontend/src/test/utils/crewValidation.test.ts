import { describe, it, expect } from 'vitest';
import { countCrewNodes, isGraphChatEligible, getGraphChatIneligibilityReason } from '@/utils/validation';

describe('Crew Validation Functions', () => {
  describe('countCrewNodes', () => {
    it('should count crew nodes correctly', () => {
      const graphData = {
        nodes: [
          { id: '1', type: 'crew', data: {} },
          { id: '2', type: 'agent', data: {} },
          { id: '3', type: 'crew', data: {} },
        ]
      };
      
      expect(countCrewNodes(graphData)).toBe(2);
    });

    it('should handle graph_data structure', () => {
      const graphData = {
        graph_data: {
          nodes: [
            { id: '1', type: 'crew', data: {} },
            { id: '2', type: 'task', data: {} },
          ]
        }
      };
      
      expect(countCrewNodes(graphData)).toBe(1);
    });

    it('should return 0 for empty or null data', () => {
      expect(countCrewNodes(null)).toBe(0);
      expect(countCrewNodes({})).toBe(0);
      expect(countCrewNodes({ nodes: [] })).toBe(0);
    });
  });

  describe('isGraphChatEligible', () => {
    it('should return true for graphs with exactly one crew', () => {
      const graphData = {
        nodes: [
          { id: '1', type: 'crew', data: {} },
          { id: '2', type: 'agent', data: {} },
        ]
      };
      
      expect(isGraphChatEligible(graphData)).toBe(true);
    });

    it('should return false for graphs with no crews', () => {
      const graphData = {
        nodes: [
          { id: '1', type: 'agent', data: {} },
          { id: '2', type: 'task', data: {} },
        ]
      };
      
      expect(isGraphChatEligible(graphData)).toBe(false);
    });

    it('should return false for graphs with multiple crews', () => {
      const graphData = {
        nodes: [
          { id: '1', type: 'crew', data: {} },
          { id: '2', type: 'crew', data: {} },
        ]
      };
      
      expect(isGraphChatEligible(graphData)).toBe(false);
    });
  });

  describe('getGraphChatIneligibilityReason', () => {
    it('should return null for eligible graphs', () => {
      const graphData = {
        nodes: [{ id: '1', type: 'crew', data: {} }]
      };
      
      expect(getGraphChatIneligibilityReason(graphData)).toBeNull();
    });

    it('should return appropriate message for graphs with no crews', () => {
      const graphData = {
        nodes: [{ id: '1', type: 'agent', data: {} }]
      };
      
      const reason = getGraphChatIneligibilityReason(graphData);
      expect(reason).toContain('no crew nodes');
    });

    it('should return appropriate message for graphs with multiple crews', () => {
      const graphData = {
        nodes: [
          { id: '1', type: 'crew', data: {} },
          { id: '2', type: 'crew', data: {} },
        ]
      };
      
      const reason = getGraphChatIneligibilityReason(graphData);
      expect(reason).toContain('multiple crew nodes');
    });
  });
}); 