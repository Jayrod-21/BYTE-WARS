/**
 * Push notification utilities for BYTE Wars PWA.
 *
 * Provides:
 * - Permission request
 * - Local notification sending (for match results, wager outcomes)
 * - Service worker push subscription (stub — real push server in Phase 11)
 */

/**
 * Request notification permission from the user.
 * @returns {Promise<boolean>} Whether permission was granted.
 */
export async function requestNotificationPermission() {
  if (!('Notification' in window)) return false;
  if (Notification.permission === 'granted') return true;
  if (Notification.permission === 'denied') return false;

  const result = await Notification.requestPermission();
  return result === 'granted';
}

/**
 * Show a local notification (doesn't require push server).
 * @param {string} title - Notification title.
 * @param {object} options - Notification options.
 */
export function showNotification(title, options = {}) {
  if (!('Notification' in window) || Notification.permission !== 'granted') {
    return;
  }

  // Use service worker notification if available
  if ('serviceWorker' in navigator && navigator.serviceWorker.controller) {
    navigator.serviceWorker.ready.then((reg) => {
      reg.showNotification(title, {
        icon: '/icon-192.png',
        badge: '/icon-192.png',
        vibrate: [100, 50, 100],
        ...options,
      });
    });
  } else {
    new Notification(title, {
      icon: '/icon-192.png',
      ...options,
    });
  }
}

/**
 * Notify user that a match has completed.
 * @param {string} matchId - The match ID.
 * @param {string} winnerName - The winner's name.
 */
export function notifyMatchComplete(matchId, winnerName) {
  showNotification('Match Complete!', {
    body: winnerName ? `${winnerName} wins!` : 'Match ended in a draw.',
    tag: `match-${matchId}`,
    data: `/playback/${matchId}`,
  });
}

/**
 * Notify user of a wager result.
 * @param {string} status - 'won', 'lost', or 'refunded'.
 * @param {number} amount - SOL amount.
 */
export function notifyWagerResult(status, amount) {
  const messages = {
    won: `You won ${amount.toFixed(2)} SOL!`,
    lost: `You lost ${amount.toFixed(2)} SOL.`,
    refunded: `${amount.toFixed(2)} SOL refunded.`,
  };

  showNotification('Wager Result', {
    body: messages[status] || `Wager ${status}`,
    tag: 'wager-result',
  });
}

/**
 * Check if notifications are supported and enabled.
 * @returns {boolean}
 */
export function notificationsEnabled() {
  return 'Notification' in window && Notification.permission === 'granted';
}
