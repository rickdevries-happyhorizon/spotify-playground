import { useEffect, useRef, useState } from 'react';

export function useJobPolling({
  startJob,
  pollJob,
  pollIntervalMs = 500,
  computePercent,
  isDone,
  isError,
  onComplete,
  onError,
  autoStart = true,
}) {
  const [phase, setPhase] = useState('idle');
  const [job, setJob] = useState(null);
  const [error, setError] = useState(null);
  const [displayPercent, setDisplayPercent] = useState(0);
  const targetPercent = useRef(0);
  const pollTimer = useRef(null);
  const raf = useRef(null);

  useEffect(() => {
    const tick = () => {
      setDisplayPercent((current) => {
        if (current < targetPercent.current) {
          const delta = Math.max(0.35, (targetPercent.current - current) * 0.08);
          return Math.min(targetPercent.current, current + delta);
        }
        return current;
      });
      raf.current = requestAnimationFrame(tick);
    };
    raf.current = requestAnimationFrame(tick);
    return () => {
      if (raf.current) cancelAnimationFrame(raf.current);
    };
  }, []);

  const stopPolling = () => {
    if (pollTimer.current) {
      clearInterval(pollTimer.current);
      pollTimer.current = null;
    }
  };

  const handleJobUpdate = (nextJob) => {
    setJob(nextJob);
    const percent = computePercent(nextJob);
    targetPercent.current = Math.max(targetPercent.current, percent);

    if (isError(nextJob)) {
      stopPolling();
      setPhase('error');
      setError(nextJob.message || nextJob.error || 'Job failed');
      onError?.(nextJob);
      return;
    }

    if (isDone(nextJob)) {
      stopPolling();
      setPhase('success');
      onComplete?.(nextJob);
      return;
    }

    setPhase('running');
  };

  const run = async (...args) => {
    stopPolling();
    setPhase('starting');
    setError(null);
    setJob(null);
    setDisplayPercent(0);
    targetPercent.current = 0;

    try {
      const started = await startJob(...args);
      handleJobUpdate(started);

      if (!isDone(started) && !isError(started)) {
        pollTimer.current = setInterval(async () => {
          try {
            const jobId = started.id || started.job_id;
            const status = await pollJob(jobId);
            handleJobUpdate(status);
          } catch (pollError) {
            stopPolling();
            setPhase('error');
            setError(pollError.message);
            onError?.(pollError);
          }
        }, pollIntervalMs);
      }
    } catch (startError) {
      setPhase('error');
      setError(startError.message);
      onError?.(startError);
    }
  };

  useEffect(() => {
    if (autoStart) run();
    return stopPolling;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return { phase, job, error, displayPercent, run, stopPolling };
}
