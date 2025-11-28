package com.desaysv.remotetunnel;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.util.Log;

/**
 * BroadcastReceiver для автозапуска сервиса при загрузке
 */
public class AutoBootReceiver extends BroadcastReceiver {
    private static final String TAG = "AutoBootReceiver";

    @Override
    public void onReceive(Context context, Intent intent) {
        String action = intent.getAction();
        Log.d(TAG, "Received action: " + action);

        if (Intent.ACTION_BOOT_COMPLETED.equals(action) ||
            Intent.ACTION_MY_PACKAGE_REPLACED.equals(action) ||
            Intent.ACTION_PACKAGE_REPLACED.equals(action)) {

            Log.d(TAG, "Starting AutoRemoteTunnelService");
            Intent serviceIntent = new Intent(context, AutoRemoteTunnelService.class);
            context.startService(serviceIntent);
        }
    }
}

