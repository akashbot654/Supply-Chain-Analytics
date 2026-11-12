"""Weekly inventory simulation shared by Project 2 notebooks.

Each week t, for every SKU, in this order:
  1. Receive orders due this week
  2. Review: if inventory position (on hand + on order) <= ROP, order k x Q,
     with k the smallest whole number that lifts the position above ROP.
     The order arrives `lead_time` weeks later.
  3. Sell: demand is served from on-hand stock; unmet demand is lost.
"""
import numpy as np


def simulate(rop, q, start_on_hand, demand, lead_time=1):
    """rop: one value per SKU (static policy), or an (SKU x week) array when the
    reorder point is recalculated each week from an updated forecast."""
    n, T = demand.shape
    rop = np.asarray(rop, dtype=float)
    rop_t = (lambda t: rop[:, t]) if rop.ndim == 2 else (lambda t: rop)
    on_hand = start_on_hand.astype(float).copy()
    arriving = np.zeros((n, T + lead_time))      # units due at the start of each week
    lost = np.zeros((n, T))
    received = np.zeros((n, T), dtype=bool)
    inv_avg = np.zeros((n, T))                    # (start + end of week on hand) / 2

    for t in range(T):
        received[:, t] = arriving[:, t] > 0
        on_hand += arriving[:, t]
        ip = on_hand + arriving[:, t + 1:].sum(axis=1)
        r = rop_t(t)
        need = (ip <= r) & (q > 0)
        k = np.zeros(n)
        k[need] = np.floor((r[need] - ip[need]) / q[need]) + 1
        arriving[:, t + lead_time] += k * q
        start = on_hand.copy()
        sold = np.minimum(on_hand, demand[:, t])
        lost[:, t] = demand[:, t] - sold
        on_hand -= sold
        inv_avg[:, t] = (start + on_hand) / 2
    return {"lost": lost, "received": received, "inv_avg": inv_avg}


def cycle_counts(lost, received):
    """Per SKU: complete replenishment cycles (receipt to receipt) and how many had lost sales."""
    n_cyc = np.zeros(len(lost), dtype=int)
    n_bad = np.zeros(len(lost), dtype=int)
    for i in range(len(lost)):
        prev = 0
        for t in np.flatnonzero(received[i]):
            n_cyc[i] += 1
            n_bad[i] += lost[i, prev:t].sum() > 0
            prev = t
    return n_cyc, n_bad
