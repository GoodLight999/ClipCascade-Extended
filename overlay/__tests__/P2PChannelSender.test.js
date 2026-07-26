import { sendP2PFragment } from '../P2PChannelSender';

const channel = (bufferedAmount = 0) => ({
  readyState: 'open',
  bufferedAmount,
  send: jest.fn(),
});

describe('sendP2PFragment', () => {
  test('sends to all open peers after checking capacity', async () => {
    const first = channel();
    const second = channel();
    await sendP2PFragment([first, second], 'fragment');
    expect(first.send).toHaveBeenCalledWith('fragment');
    expect(second.send).toHaveBeenCalledWith('fragment');
  });

  test('waits until every peer buffer is below the high-water mark', async () => {
    const slow = channel(5000);
    const fast = channel(0);
    const sleep = jest.fn(async () => {
      slow.bufferedAmount = 0;
    });
    await sendP2PFragment([slow, fast], 'fragment', {
      highWaterMark: 1000,
      sleep,
      now: () => 0,
    });
    expect(sleep).toHaveBeenCalled();
    expect(slow.send).toHaveBeenCalledTimes(1);
    expect(fast.send).toHaveBeenCalledTimes(1);
  });

  test('does not partially send when a peer is already closed', async () => {
    const open = channel();
    const closed = channel();
    closed.readyState = 'closed';
    await expect(sendP2PFragment([open, closed], 'fragment')).rejects.toThrow(
      'closed during send',
    );
    expect(open.send).not.toHaveBeenCalled();
  });

  test('times out instead of growing a stalled buffer forever', async () => {
    const stalled = channel(5000);
    let time = 0;
    const sleep = async ms => {
      time += ms;
    };
    await expect(
      sendP2PFragment([stalled], 'fragment', {
        highWaterMark: 1000,
        timeoutMs: 50,
        pollMs: 25,
        sleep,
        now: () => time,
      }),
    ).rejects.toThrow('backpressure timeout');
    expect(stalled.send).not.toHaveBeenCalled();
  });
});
