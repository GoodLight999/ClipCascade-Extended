import {
  classifyOutboundDeliveryResult,
  resolveAwaitingReceiptHead,
} from './OutboundDeliveryPolicy';

/**
 * Apply one transport outcome to the durable queue. This function deliberately
 * re-reads the queue after an awaiting-receipt result because the receipt
 * callback may have acknowledged the head before the send Promise returned.
 */
export async function applyOutboundDeliveryResult({
  deliveryId,
  transportResult,
  peek,
  acknowledge,
  updateStatus,
}) {
  if (typeof peek !== 'function' || typeof acknowledge !== 'function') {
    throw new TypeError('Outbound delivery executor requires queue functions');
  }
  if (typeof updateStatus !== 'function') {
    throw new TypeError('Outbound delivery executor requires a status updater');
  }

  const delivery = classifyOutboundDeliveryResult(transportResult);
  if (delivery.action === 'wait') {
    await updateStatus(delivery.status);
    return {action: 'wait', status: delivery.status};
  }
  if (delivery.action === 'await-receipt') {
    const currentHead = await peek();
    const resolution = resolveAwaitingReceiptHead(
      deliveryId,
      currentHead?.id || null,
    );
    await updateStatus(resolution.status);
    return resolution;
  }

  await acknowledge(deliveryId);
  await updateStatus(delivery.status);
  return {action: 'continue', status: delivery.status};
}
