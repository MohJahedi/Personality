import { useCallback, useEffect, useState } from 'react';
import { get } from './api';
export function useResource<T>(path: string | null) {
    const [data, setData] = useState<T>();
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const refresh = useCallback(async () => {
        if (!path)
            return;
        setLoading(true);
        setError('');
        try {
            setData(await get<T>(path));
        }
        catch (e) {
            setError(e instanceof Error ? e.message : 'ارتباط برقرار نشد.');
        }
        finally {
            setLoading(false);
        }
    }, [path]);
    useEffect(() => {
        setData(undefined);
        setError('');
        if (!path)
            return;
        const controller = new AbortController();
        setLoading(true);
        get<T>(path, controller.signal).then(setData).catch(e => {
            if (!controller.signal.aborted)
                setError(e instanceof Error ? e.message : 'ارتباط برقرار نشد.');
        }).finally(() => { if (!controller.signal.aborted)
            setLoading(false); });
        return () => controller.abort();
    }, [path]);
    return { data, error, loading, refresh };
}
