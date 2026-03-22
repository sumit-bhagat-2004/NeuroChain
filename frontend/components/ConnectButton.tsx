'use client';

import { useWallet } from '@/lib/WalletContext';

export default function LoginButton() {
  const { accountAddress, connectWallet, disconnectWallet } = useWallet();

  return (
    <div className="flex items-center gap-2">
      {accountAddress ? (
        <>
          <div className="px-3 py-2 bg-purple-900/50 border border-purple-700 rounded-lg text-xs text-purple-200">
            {accountAddress.slice(0, 6)}...{accountAddress.slice(-4)}
          </div>
          <button
            onClick={disconnectWallet}
            className="px-3 py-2 bg-gray-800 hover:bg-gray-700 text-white rounded-lg transition-colors text-xs font-medium"
          >
            Disconnect
          </button>
        </>
      ) : (
        <button
          onClick={connectWallet}
          className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors text-sm font-medium"
        >
          Connect Wallet
        </button>
      )}
    </div>
  );
}
