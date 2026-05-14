/**
 * API client for BYTE Wars backend.
 * Handles all HTTP requests and JWT token management.
 */

const API_BASE = '/api';

function getToken() {
  return localStorage.getItem('bw_token');
}

function setToken(token) {
  localStorage.setItem('bw_token', token);
}

function clearToken() {
  localStorage.removeItem('bw_token');
}

function getUser() {
  const raw = localStorage.getItem('bw_user');
  return raw ? JSON.parse(raw) : null;
}

function setUser(user) {
  localStorage.setItem('bw_user', JSON.stringify(user));
}

function clearUser() {
  localStorage.removeItem('bw_user');
}

async function request(path, options = {}) {
  const headers = { 'Content-Type': 'application/json', ...options.headers };
  const token = getToken();
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  const resp = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ detail: resp.statusText }));
    throw new Error(err.detail || `HTTP ${resp.status}`);
  }
  return resp.json();
}

// --- Auth ---
export async function register(username, password) {
  const data = await request('/auth/register', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  });
  setToken(data.token);
  setUser(data.user);
  return data;
}

export async function login(username, password) {
  const data = await request('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  });
  setToken(data.token);
  setUser(data.user);
  return data;
}

export function logout() {
  clearToken();
  clearUser();
}

export async function getMe() {
  return request('/auth/me');
}

// --- Champions ---
export async function listChampions(archetype) {
  const query = archetype ? `?archetype=${archetype}` : '';
  return request(`/champions${query}`);
}

export async function getChampion(id) {
  return request(`/champions/${id}`);
}

export async function createChampion(data) {
  return request('/champions', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function updateChampion(id, data) {
  return request(`/champions/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
}

// --- Matches ---
export async function listMatches(status) {
  const query = status ? `?status=${status}` : '';
  return request(`/matches${query}`);
}

export async function getMatch(id) {
  return request(`/matches/${id}`);
}

export async function createMatch(championIds) {
  return request('/matches', {
    method: 'POST',
    body: JSON.stringify({ champion_ids: championIds }),
  });
}

export async function startMatch(id) {
  return request(`/matches/${id}/start`, { method: 'POST' });
}

// --- Playback ---
export async function getPlayback(matchId) {
  return request(`/playback/${matchId}`);
}

export function getPlaybackUrl(matchId) {
  return `${API_BASE}/playback/${matchId}/watch`;
}

// --- Wagers ---
export async function placeWager(matchId, userId, walletAddress, championId, amountSol) {
  return request('/wagers/place', {
    method: 'POST',
    body: JSON.stringify({
      match_id: matchId,
      user_id: userId,
      wallet_address: walletAddress,
      champion_id: championId,
      amount_sol: amountSol,
    }),
  });
}

export async function cancelWager(wagerId, userId) {
  return request(`/wagers/${wagerId}/cancel`, {
    method: 'POST',
    body: JSON.stringify({ user_id: userId }),
  });
}

export async function getMatchWagers(matchId) {
  return request(`/wagers/match/${matchId}`);
}

export async function getUserWagers(userId) {
  return request(`/wagers/user/${userId}`);
}

export async function getMatchOdds(matchId) {
  return request(`/wagers/odds/${matchId}`);
}

export async function getWalletBalance(walletAddress) {
  return request(`/wagers/wallet/${walletAddress}`);
}

export async function airdropSol(walletAddress, amountSol = 10) {
  return request(`/wagers/wallet/${walletAddress}/airdrop`, {
    method: 'POST',
    body: JSON.stringify({ amount_sol: amountSol }),
  });
}

// --- Marketplace ---
export async function browseMarketplace(filters = {}) {
  const params = new URLSearchParams();
  if (filters.nft_type) params.set('nft_type', filters.nft_type);
  if (filters.rarity) params.set('rarity', filters.rarity);
  if (filters.archetype) params.set('archetype', filters.archetype);
  const query = params.toString() ? `?${params}` : '';
  return request(`/nft/marketplace/browse${query}`);
}

export async function createListing(nftId, sellerId, priceSol) {
  return request('/nft/marketplace/list', {
    method: 'POST',
    body: JSON.stringify({ nft_id: nftId, seller_id: sellerId, price_sol: priceSol }),
  });
}

export async function cancelListing(listingId, sellerId) {
  return request(`/nft/marketplace/${listingId}/cancel`, {
    method: 'POST',
    body: JSON.stringify({ seller_id: sellerId }),
  });
}

export async function buyListing(listingId, buyerId, buyerWallet) {
  return request(`/nft/marketplace/${listingId}/buy`, {
    method: 'POST',
    body: JSON.stringify({ buyer_id: buyerId, buyer_wallet: buyerWallet }),
  });
}

export async function getNFTDetail(nftId) {
  return request(`/nft/${nftId}/detail`);
}

export async function getUserChests(ownerId) {
  return request(`/nft/chests/${ownerId}`);
}

export async function getInventory(ownerId) {
  return request(`/nft/inventory/${ownerId}`);
}

export async function generateInventory(ownerId) {
  return request(`/nft/inventory/${ownerId}/generate`, { method: 'POST' });
}

export async function transferNFT(nftId, fromOwner, toOwner) {
  return request('/nft/transfer', {
    method: 'POST',
    body: JSON.stringify({ nft_id: nftId, from_owner: fromOwner, to_owner: toOwner }),
  });
}

export function walletForUser(user) {
  if (!user) return null;
  return user.wallet_address || `devnet_${user.id}`;
}

export { getToken, getUser, setToken, setUser };
