'use client';

import React, { useState, useEffect } from 'react';
import { useWallet } from '@/lib/WalletContext';
import {
  createDebateSession,
  CreateDebateSessionRequest,
  DebateSessionParticipant,
  DebateSessionResponse,
} from '@/lib/api';

interface DebateSessionCreatorProps {
  onSessionCreated: (session: DebateSessionResponse) => void;
}

export default function DebateSessionCreator({
  onSessionCreated,
}: DebateSessionCreatorProps) {
  const { accountAddress, isConnected } = useWallet();

  const [topicName, setTopicName] = useState('');
  const [creatorNames, setCreatorNames] = useState<string[]>(['']);
  const [participants, setParticipants] = useState<DebateSessionParticipant[]>([
    { name: '', wallet_address: '' },
  ]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleAddCreatorName = () => {
    setCreatorNames([...creatorNames, '']);
  };

  const handleRemoveCreatorName = (index: number) => {
    const newNames = creatorNames.filter((_, i) => i !== index);
    setCreatorNames(newNames.length > 0 ? newNames : ['']);
  };

  const handleCreatorNameChange = (index: number, value: string) => {
    const newNames = [...creatorNames];
    newNames[index] = value;
    setCreatorNames(newNames);
  };

  const handleAddParticipant = () => {
    setParticipants([...participants, { name: '', wallet_address: '' }]);
  };

  const handleRemoveParticipant = (index: number) => {
    const newParticipants = participants.filter((_, i) => i !== index);
    setParticipants(newParticipants.length > 0 ? newParticipants : [{ name: '', wallet_address: '' }]);
  };

  const handleParticipantChange = (
    index: number,
    field: 'name' | 'wallet_address',
    value: string
  ) => {
    const newParticipants = [...participants];
    newParticipants[index] = { ...newParticipants[index], [field]: value };
    setParticipants(newParticipants);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!isConnected || !accountAddress) {
      setError('Please connect your wallet first');
      return;
    }

    // Validation
    if (!topicName.trim()) {
      setError('Topic name is required');
      return;
    }

    const validCreatorNames = creatorNames.filter((name) => name.trim());
    if (validCreatorNames.length === 0) {
      setError('At least one creator name is required');
      return;
    }

    const validParticipants = participants.filter((p) => p.wallet_address.trim());
    if (validParticipants.length === 0) {
      setError('At least one participant with wallet address is required');
      return;
    }

    setIsLoading(true);

    try {
      const request: CreateDebateSessionRequest = {
        topic_name: topicName.trim(),
        creator_wallet: accountAddress,
        creator_names: validCreatorNames,
        participants: validParticipants.map((p) => ({
          name: p.name?.trim() || undefined,
          wallet_address: p.wallet_address.trim(),
        })),
      };

      const response = await createDebateSession(request);
      onSessionCreated(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create debate session');
    } finally {
      setIsLoading(false);
    }
  };

  if (!isConnected) {
    return (
      <div className="max-w-3xl mx-auto">
        <div className="bg-amber-900/50 border border-amber-700 rounded-lg p-6 text-center">
          <p className="text-amber-200 font-medium mb-2">Wallet Connection Required</p>
          <p className="text-amber-100 text-sm">
            Please connect your Pera wallet from the top-right button to create a debate session.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto">
      <div className="bg-gray-800 border border-gray-700 rounded-lg p-6">
        <h2 className="text-2xl font-bold text-purple-400 mb-2">Create Debate Session</h2>
        <p className="text-gray-400 text-sm mb-6">
          Initialize a new debate with topic, creators, and participants. Only the creator and
          participants will be able to contribute to this session.
        </p>

        {error && (
          <div className="mb-4 bg-red-900/50 border border-red-700 text-red-200 px-4 py-3 rounded-lg">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Topic Name */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Topic / Debate Title <span className="text-red-400">*</span>
            </label>
            <input
              type="text"
              value={topicName}
              onChange={(e) => setTopicName(e.target.value)}
              placeholder="e.g., AI Ethics in Healthcare"
              className="w-full bg-gray-900 text-white border border-gray-700 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500"
              disabled={isLoading}
            />
          </div>

          {/* Creator Wallet - Read Only */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Creator Wallet Address <span className="text-red-400">*</span>
            </label>
            <div className="w-full bg-gray-900 text-gray-300 border border-gray-700 rounded-lg px-4 py-2 font-mono text-sm flex items-center justify-between">
              <span>{accountAddress}</span>
              <span className="text-xs bg-purple-600/30 text-purple-300 px-2 py-1 rounded">
                From Pera
              </span>
            </div>
            <p className="text-xs text-gray-500 mt-1">
              Your connected Pera wallet address (auto-filled and cannot be changed)
            </p>
          </div>

          {/* Creator Names */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Creator Names <span className="text-red-400">*</span>
            </label>
            {creatorNames.map((name, index) => (
              <div key={index} className="flex gap-2 mb-2">
                <input
                  type="text"
                  value={name}
                  onChange={(e) => handleCreatorNameChange(index, e.target.value)}
                  placeholder="e.g., Alice"
                  className="flex-1 bg-gray-900 text-white border border-gray-700 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500"
                  disabled={isLoading}
                />
                {creatorNames.length > 1 && (
                  <button
                    type="button"
                    onClick={() => handleRemoveCreatorName(index)}
                    className="px-3 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors"
                    disabled={isLoading}
                  >
                    Remove
                  </button>
                )}
              </div>
            ))}
            <button
              type="button"
              onClick={handleAddCreatorName}
              className="text-sm text-purple-400 hover:text-purple-300 transition-colors"
              disabled={isLoading}
            >
              + Add Creator Name
            </button>
          </div>

          {/* Participants */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Participants <span className="text-red-400">*</span>
            </label>
            <p className="text-xs text-gray-500 mb-3">
              Add participants who can contribute to this debate. Wallet address is required.
            </p>
            {participants.map((participant, index) => (
              <div key={index} className="bg-gray-900 border border-gray-700 rounded-lg p-4 mb-3">
                <div className="space-y-3">
                  <input
                    type="text"
                    value={participant.name}
                    onChange={(e) => handleParticipantChange(index, 'name', e.target.value)}
                    placeholder="Participant Name (optional)"
                    className="w-full bg-gray-800 text-white border border-gray-700 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500"
                    disabled={isLoading}
                  />
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={participant.wallet_address}
                      onChange={(e) =>
                        handleParticipantChange(index, 'wallet_address', e.target.value)
                      }
                      placeholder="Wallet Address (required) 0x..."
                      className="flex-1 bg-gray-800 text-white border border-gray-700 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500"
                      disabled={isLoading}
                    />
                    {participants.length > 1 && (
                      <button
                        type="button"
                        onClick={() => handleRemoveParticipant(index)}
                        className="px-3 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors"
                        disabled={isLoading}
                      >
                        Remove
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))}
            <button
              type="button"
              onClick={handleAddParticipant}
              className="text-sm text-purple-400 hover:text-purple-300 transition-colors"
              disabled={isLoading}
            >
              + Add Participant
            </button>
          </div>

          {/* Submit Button */}
          <div className="flex gap-3 pt-4">
            <button
              type="submit"
              disabled={isLoading}
              className="flex-1 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-700 disabled:cursor-not-allowed text-white font-medium py-3 px-6 rounded-lg transition-colors"
            >
              {isLoading ? 'Creating Session...' : 'Create Debate Session'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
