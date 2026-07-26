"""Supervise Promise-returning work invoked by timer/WebRTC callback APIs.

These host APIs ignore returned Promises. Every asynchronous callback therefore
enters a common detached-task boundary that records failures without creating a
second unhandled rejection if AsyncStorage itself is unavailable.
"""
from __future__ import annotations

from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one marker, found {count}")
    return text.replace(old, new, 1)


def apply(root: Path) -> None:
    path = root / "StartForegroundService.js"
    text = path.read_text(encoding="utf-8")

    text = replace_once(
        text,
        """const activeClipboardSubscriptions = new Set();""",
        """function runDetached(scope, task) {
  Promise.resolve()
    .then(task)
    .catch(error => {
      const detail = `${scope}:${String(error?.stack || error)}`.slice(0, 4000);
      return Promise.all([
        setDataInAsyncStorage('foreground_service_detached_error', detail),
        setDataInAsyncStorage(
          'foreground_service_detached_error_at',
          String(Date.now()),
        ),
      ]).catch(() => undefined);
    });
}

const activeClipboardSubscriptions = new Set();""",
        "detached callback supervisor",
    )

    text = replace_once(
        text,
        """        await setDataInAsyncStorage('foreground_service_state', 'handler-starting');
        await setDataInAsyncStorage('foreground_service_error', '');""",
        """        await setDataInAsyncStorage('foreground_service_state', 'handler-starting');
        await setDataInAsyncStorage('foreground_service_error', '');
        await setDataInAsyncStorage('foreground_service_detached_error', '');
        await setDataInAsyncStorage('foreground_service_detached_error_at', '');""",
        "clear detached callback evidence on runtime start",
    )

    text = replace_once(
        text,
        """          outboundRetryTimer = setTimeout(() => {
            outboundRetryTimer = null;
            flushOutboundQueue();
          }, delay);""",
        """          outboundRetryTimer = setTimeout(() => {
            outboundRetryTimer = null;
            runDetached('outbound-retry', flushOutboundQueue);
          }, delay);""",
        "supervised outbound retry timer",
    )

    text = replace_once(
        text,
        """              setTimeout(() => disposePeerConnection(peerId), 0);""",
        """              setTimeout(() => {
                runDetached(
                  `quarantine-dispose:${peerId}`,
                  () => disposePeerConnection(peerId),
                );
              }, 0);""",
        "supervised quarantine disposal",
    )

    text = replace_once(
        text,
        """            signalingReconnectTimer = setTimeout(() => {
              signalingReconnectTimer = null;
              void (async () => {
                if (
                  wsSignalingClient == null &&
                  (await getDataFromAsyncStorage('wsIsRunning')) === 'true'
                ) {
                  await startSignalingConnection();
                }
              })().catch(error => recordSignalingFailure('reconnect', error));
            }, RECONNECT_WS_TIMER);""",
        """            signalingReconnectTimer = setTimeout(() => {
              signalingReconnectTimer = null;
              runDetached('signaling-reconnect', async () => {
                if (
                  wsSignalingClient == null &&
                  (await getDataFromAsyncStorage('wsIsRunning')) === 'true'
                ) {
                  await startSignalingConnection();
                }
              });
            }, RECONNECT_WS_TIMER);""",
        "supervised signaling reconnect timer",
    )

    text = replace_once(
        text,
        """              wsSignalingClient.onopen = async () => {
                clearSignalingReconnect();
                await setDataInAsyncStorage('p2p_last_signaling_error', '');
                await cleanupPeerConnections();

                await setDataInAsyncStorage(
                  'wsStatusMessage',
                  '✅ Signaling connected; waiting for peer',
                );

                if (enable_websocket_status_notification === 'true') {
                  if (websocket_status_notification_toggle === true) {
                    websocket_status_notification_toggle = false;
                    await showWebSocketStatusNotification(
                      'WebSocket Connection Restored 🔗',
                    );
                  } else {
                    await notifee.cancelNotification(
                      'ClipCascade_WebSocket_Status_Notification_Id',
                    );
                  }
                }
              };""",
        """              wsSignalingClient.onopen = () => {
                runDetached('signaling-open', async () => {
                  clearSignalingReconnect();
                  await setDataInAsyncStorage('p2p_last_signaling_error', '');
                  await cleanupPeerConnections();

                  await setDataInAsyncStorage(
                    'wsStatusMessage',
                    '✅ Signaling connected; waiting for peer',
                  );

                  if (enable_websocket_status_notification === 'true') {
                    if (websocket_status_notification_toggle === true) {
                      websocket_status_notification_toggle = false;
                      await showWebSocketStatusNotification(
                        'WebSocket Connection Restored 🔗',
                      );
                    } else {
                      await notifee.cancelNotification(
                        'ClipCascade_WebSocket_Status_Notification_Id',
                      );
                    }
                  }
                });
              };""",
        "supervised signaling open callback",
    )

    text = replace_once(
        text,
        """              wsSignalingClient.onmessage = async event => {
                try {
                  const data = JSON.parse(event.data);
                  switch (data.type) {
                    case 'ASSIGNED_ID':
                      if (myPeerId && myPeerId !== data.peerId) {
                        await cleanupPeerConnections();
                      }
                      myPeerId = data.peerId;
                      if (pendingPeerList != null) {
                        const pending = pendingPeerList;
                        pendingPeerList = null;
                        await handlePeerList(pending);
                      }
                      break;

                    case 'PEER_LIST':
                      await handlePeerList(data.peers);
                      break;

                    case 'OFFER': {
                      const compatibility = evaluateP2PCompatibility(
                        localCompatibility,
                        data.compatibility,
                      );
                      await markPeerCompatibility(
                        data.fromPeerId,
                        compatibility.state,
                        compatibility.reason,
                      );
                      if (compatibility.state !== 'incompatible') {
                        await handleOffer(data.fromPeerId, data.offer);
                      }
                      break;
                    }

                    case 'ANSWER': {
                      const compatibility = evaluateP2PCompatibility(
                        localCompatibility,
                        data.compatibility,
                      );
                      await markPeerCompatibility(
                        data.fromPeerId,
                        compatibility.state,
                        compatibility.reason,
                      );
                      if (compatibility.state !== 'incompatible') {
                        await handleAnswer(data.fromPeerId, data.answer);
                      }
                      break;
                    }

                    case 'ICE_CANDIDATE':
                      await handleIceCandidate(data.fromPeerId, data.candidate);
                      break;
                  }

                  await setDataInAsyncStorage(
                    'wsStatusMessage',
                    liveConnectionsCount > 0
                      ? '✅ P2P peer connected'
                      : '✅ Signaling connected; waiting for peer',
                  );
                } catch (e) {
                  await setDataInAsyncStorage(
                    'wsStatusMessage',
                    '❌ Inbound Error: ' + e,
                  );
                }
              };""",
        """              wsSignalingClient.onmessage = event => {
                runDetached('signaling-message', async () => {
                  try {
                    const data = JSON.parse(event.data);
                    switch (data.type) {
                      case 'ASSIGNED_ID':
                        if (myPeerId && myPeerId !== data.peerId) {
                          await cleanupPeerConnections();
                        }
                        myPeerId = data.peerId;
                        if (pendingPeerList != null) {
                          const pending = pendingPeerList;
                          pendingPeerList = null;
                          await handlePeerList(pending);
                        }
                        break;

                      case 'PEER_LIST':
                        await handlePeerList(data.peers);
                        break;

                      case 'OFFER': {
                        const compatibility = evaluateP2PCompatibility(
                          localCompatibility,
                          data.compatibility,
                        );
                        await markPeerCompatibility(
                          data.fromPeerId,
                          compatibility.state,
                          compatibility.reason,
                        );
                        if (compatibility.state !== 'incompatible') {
                          await handleOffer(data.fromPeerId, data.offer);
                        }
                        break;
                      }

                      case 'ANSWER': {
                        const compatibility = evaluateP2PCompatibility(
                          localCompatibility,
                          data.compatibility,
                        );
                        await markPeerCompatibility(
                          data.fromPeerId,
                          compatibility.state,
                          compatibility.reason,
                        );
                        if (compatibility.state !== 'incompatible') {
                          await handleAnswer(data.fromPeerId, data.answer);
                        }
                        break;
                      }

                      case 'ICE_CANDIDATE':
                        await handleIceCandidate(data.fromPeerId, data.candidate);
                        break;
                    }

                    await setDataInAsyncStorage(
                      'wsStatusMessage',
                      liveConnectionsCount > 0
                        ? '✅ P2P peer connected'
                        : '✅ Signaling connected; waiting for peer',
                    );
                  } catch (e) {
                    await setDataInAsyncStorage(
                      'wsStatusMessage',
                      '❌ Inbound Error: ' + e,
                    );
                  }
                });
              };""",
        "supervised signaling message callback",
    )

    text = replace_once(
        text,
        """              wsSignalingClient.onerror = async event => {
                block_image_once = false;
                await setDataInAsyncStorage(
                  'wsStatusMessage',
                  '❌ WebSocket Error: ' + JSON.stringify(event, null, 2),
                );
              };""",
        """              wsSignalingClient.onerror = event => {
                runDetached('signaling-error', async () => {
                  block_image_once = false;
                  await setDataInAsyncStorage(
                    'wsStatusMessage',
                    '❌ WebSocket Error: ' + JSON.stringify(event, null, 2),
                  );
                });
              };""",
        "supervised signaling error callback",
    )

    text = replace_once(
        text,
        """              wsSignalingClient.onclose = async event => {
                block_image_once = false;
                const reason = event?.reason || 'closed by client';
                await setDataInAsyncStorage(
                  'wsStatusMessage',
                  '⚠️ WebSocket Close: ' + reason,
                );
                if (
                  enable_websocket_status_notification === 'true' &&
                  websocket_status_notification_toggle === false &&
                  (await getDataFromAsyncStorage('wsIsRunning')) === 'true'
                ) {
                  websocket_status_notification_toggle = true;
                  await showWebSocketStatusNotification(
                    'WebSocket Connection Lost ⛓️‍💥',
                    -1,
                  );
                }

                wsSignalingClient = null;
                scheduleSignalingReconnect();
              };""",
        """              wsSignalingClient.onclose = event => {
                runDetached('signaling-close', async () => {
                  block_image_once = false;
                  const reason = event?.reason || 'closed by client';
                  await setDataInAsyncStorage(
                    'wsStatusMessage',
                    '⚠️ WebSocket Close: ' + reason,
                  );
                  if (
                    enable_websocket_status_notification === 'true' &&
                    websocket_status_notification_toggle === false &&
                    (await getDataFromAsyncStorage('wsIsRunning')) === 'true'
                  ) {
                    websocket_status_notification_toggle = true;
                    await showWebSocketStatusNotification(
                      'WebSocket Connection Lost ⛓️‍💥',
                      -1,
                    );
                  }

                  wsSignalingClient = null;
                  scheduleSignalingReconnect();
                });
              };""",
        "supervised signaling close callback",
    )

    text = replace_once(
        text,
        """            pc.onicecandidate = async event => {
              if (event.candidate) {
                await signalingSend({
                  type: 'ICE_CANDIDATE',
                  fromPeerId: myPeerId,
                  toPeerId: remotePeerId,
                  candidate: event.candidate,
                });
              }
            };

            pc.ondatachannel = async event => {
              const channel = event.channel;
              dataChannels[remotePeerId] = channel;
              await setupDataChannel(remotePeerId, channel);
            };

            pc.onconnectionstatechange = () => {
              const st = pc.connectionState;
              if (st === 'failed' || st === 'closed') {
                recoverPeerTransport(remotePeerId, pc);
              }
            };""",
        """            pc.onicecandidate = event => {
              if (!event.candidate) return;
              runDetached(`ice-candidate:${remotePeerId}`, () =>
                signalingSend({
                  type: 'ICE_CANDIDATE',
                  fromPeerId: myPeerId,
                  toPeerId: remotePeerId,
                  candidate: event.candidate,
                }),
              );
            };

            pc.ondatachannel = event => {
              const channel = event.channel;
              dataChannels[remotePeerId] = channel;
              runDetached(`datachannel-received:${remotePeerId}`, () =>
                setupDataChannel(remotePeerId, channel),
              );
            };

            pc.onconnectionstatechange = () => {
              const st = pc.connectionState;
              if (st === 'failed' || st === 'closed') {
                runDetached(`peer-recovery:${remotePeerId}`, () =>
                  recoverPeerTransport(remotePeerId, pc),
                );
              }
            };""",
        "supervised RTCPeerConnection callbacks",
    )

    text = replace_once(
        text,
        """            channel.onopen = async () => {
              if (!compatibilityByPeer.has(remotePeerId)) {
                compatibilityByPeer.set(remotePeerId, 'unknown');
              }
              startDataChannelHeartbeat(remotePeerId, channel);
              await syncLiveConnectionsCount();
              await setDataInAsyncStorage(
                'wsStatusMessage',
                '✅ P2P peer connected',
              );
              await flushOutboundQueue();
            };

            channel.onmessage = async e => {
              await onDataChannelMessage(e.data, remotePeerId);
            };

            channel.onclose = async () => {
              if (dataChannelHeartbeatTimers[remotePeerId]) {
                clearInterval(dataChannelHeartbeatTimers[remotePeerId]);
                delete dataChannelHeartbeatTimers[remotePeerId];
              }
              await syncLiveConnectionsCount();
              if (liveConnectionsCount === 0) {
                await setDataInAsyncStorage(
                  'wsStatusMessage',
                  '✅ Signaling connected; waiting for peer',
                );
              }
              if (!quarantinedPeers.has(remotePeerId)) {
                await recoverPeerTransport(remotePeerId, null);
              }
            };

            channel.onerror = async err => {
              p2pMsg = '❌ DataChannel error with ' + remotePeerId + ': ' + err;
              await p2pStatusMessageChanged();
            };""",
        """            channel.onopen = () => {
              runDetached(`datachannel-open:${remotePeerId}`, async () => {
                if (!compatibilityByPeer.has(remotePeerId)) {
                  compatibilityByPeer.set(remotePeerId, 'unknown');
                }
                startDataChannelHeartbeat(remotePeerId, channel);
                await syncLiveConnectionsCount();
                await setDataInAsyncStorage(
                  'wsStatusMessage',
                  '✅ P2P peer connected',
                );
                await flushOutboundQueue();
              });
            };

            channel.onmessage = e => {
              runDetached(`datachannel-message:${remotePeerId}`, () =>
                onDataChannelMessage(e.data, remotePeerId),
              );
            };

            channel.onclose = () => {
              runDetached(`datachannel-close:${remotePeerId}`, async () => {
                if (dataChannelHeartbeatTimers[remotePeerId]) {
                  clearInterval(dataChannelHeartbeatTimers[remotePeerId]);
                  delete dataChannelHeartbeatTimers[remotePeerId];
                }
                await syncLiveConnectionsCount();
                if (liveConnectionsCount === 0) {
                  await setDataInAsyncStorage(
                    'wsStatusMessage',
                    '✅ Signaling connected; waiting for peer',
                  );
                }
                if (!quarantinedPeers.has(remotePeerId)) {
                  await recoverPeerTransport(remotePeerId, null);
                }
              });
            };

            channel.onerror = err => {
              runDetached(`datachannel-error:${remotePeerId}`, async () => {
                p2pMsg = '❌ DataChannel error with ' + remotePeerId + ': ' + err;
                await p2pStatusMessageChanged();
              });
            };""",
        "supervised RTCDataChannel callbacks",
    )

    path.write_text(text, encoding="utf-8")
