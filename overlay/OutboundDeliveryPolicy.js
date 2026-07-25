export const OUTBOUND_DELIVERY = Object.freeze({
  WAITING: 'waiting-for-transport',
  SENT: 'sent',
  AWAITING_P2S_RECEIPT: 'awaiting-p2s-receipt',
  FEEDBACK_SUPPRESSED: 'feedback-suppressed',
  POLICY_DISCARDED: 'policy-discarded',
});

const TERMINAL_RESULTS = new Set([
  OUTBOUND_DELIVERY.SENT,
  OUTBOUND_DELIVERY.FEEDBACK_SUPPRESSED,
  OUTBOUND_DELIVERY.POLICY_DISCARDED,
]);

export function classifyOutboundDeliveryResult(result) {
  if (
    result === OUTBOUND_DELIVERY.WAITING ||
    result === false ||
    result == null
  ) {
    return {action: 'wait', status: OUTBOUND_DELIVERY.WAITING};
  }
  if (result === OUTBOUND_DELIVERY.AWAITING_P2S_RECEIPT) {
    return {action: 'await-receipt', status: result};
  }
  if (TERMINAL_RESULTS.has(result)) {
    return {action: 'acknowledge', status: result};
  }
  throw new Error(`Invalid outbound delivery result: ${String(result)}`);
}

/**
 * A STOMP receipt callback can acknowledge the durable head before the send
 * call returns to the active flush loop. Re-read the head before deciding to
 * stop: if the delivery ID has already disappeared, the same flush may continue
 * with the next item instead of waiting for another external trigger.
 */
export function resolveAwaitingReceiptHead(deliveryId, currentHeadId) {
  const id = String(deliveryId || '');
  if (!id) throw new Error('Awaiting-receipt delivery ID is required');
  return String(currentHeadId || '') === id
    ? {action: 'wait', status: OUTBOUND_DELIVERY.AWAITING_P2S_RECEIPT}
    : {action: 'continue', status: 'p2s-receipt-already-acknowledged'};
}
