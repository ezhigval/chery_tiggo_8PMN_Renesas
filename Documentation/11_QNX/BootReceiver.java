package com.desaysv.remotetunnel;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.util.Log;

/**
 * BroadcastReceiver для запуска ReverseTunnelClient при загрузке
 */
public class BootReceiver extends BroadcastReceiver {
    private static final String TAG = "BootReceiver";

    @Override
    public void onReceive(Context context, Intent intent) {
        if (Intent.ACTION_BOOT_COMPLETED.equals(intent.getAction())) {
            Log.d(TAG, "Boot completed, starting ReverseTunnelClient");

            Intent serviceIntent = new Intent(context, ReverseTunnelClient.class);
            context.startService(serviceIntent);
        }
    }
}

