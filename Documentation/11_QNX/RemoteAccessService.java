package com.desaysv.remoteaccess;

import android.app.Service;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.os.IBinder;
import android.util.Log;
import java.io.IOException;
import java.net.ServerSocket;
import java.net.Socket;

/**
 * Сервис для автоматического включения ADB TCP/IP и создания удаленного доступа
 */
public class RemoteAccessService extends Service {
    private static final String TAG = "RemoteAccessService";
    private static final int ADB_TCP_PORT = 5555;

    private BroadcastReceiver bootReceiver;
    private BroadcastReceiver networkReceiver;

    @Override
    public void onCreate() {
        super.onCreate();
        Log.d(TAG, "RemoteAccessService created");

        // Регистрация BroadcastReceiver для загрузки
        bootReceiver = new BroadcastReceiver() {
            @Override
            public void onReceive(Context context, Intent intent) {
                if (Intent.ACTION_BOOT_COMPLETED.equals(intent.getAction())) {
                    Log.d(TAG, "Boot completed, enabling remote access");
                    enableRemoteAccess();
                }
            }
        };

        // Регистрация BroadcastReceiver для изменения сети
        networkReceiver = new BroadcastReceiver() {
            @Override
            public void onReceive(Context context, Intent intent) {
                if (android.net.ConnectivityManager.CONNECTIVITY_ACTION.equals(intent.getAction())) {
                    Log.d(TAG, "Network changed, checking remote access");
                    enableRemoteAccess();
                }
            }
        };

        registerReceiver(bootReceiver, new IntentFilter(Intent.ACTION_BOOT_COMPLETED));
        registerReceiver(networkReceiver, new IntentFilter(android.net.ConnectivityManager.CONNECTIVITY_ACTION));

        // Включить удаленный доступ сразу
        enableRemoteAccess();
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        Log.d(TAG, "Service started");
        enableRemoteAccess();
        return START_STICKY; // Перезапускать при падении
    }

    private void enableRemoteAccess() {
        try {
            // 1. Включить ADB TCP/IP
            Log.d(TAG, "Enabling ADB TCP/IP on port " + ADB_TCP_PORT);
            Runtime.getRuntime().exec("setprop service.adb.tcp.port " + ADB_TCP_PORT);
            Runtime.getRuntime().exec("setprop persist.adb.tcp.port " + ADB_TCP_PORT);

            // 2. Получить IP адрес
            String ipAddress = getIpAddress();
            if (ipAddress != null && !ipAddress.isEmpty()) {
                Log.d(TAG, "Device IP address: " + ipAddress);
                Log.d(TAG, "ADB connection: adb connect " + ipAddress + ":" + ADB_TCP_PORT);

                // 3. (Опционально) Отправить IP адрес на сервер
                // sendIpToServer(ipAddress);
            } else {
                Log.w(TAG, "No IP address found, device may not be connected to network");
            }

        } catch (IOException e) {
            Log.e(TAG, "Error enabling remote access", e);
        }
    }

    private String getIpAddress() {
        try {
            // Попытка получить IP через getprop
            Process process = Runtime.getRuntime().exec("getprop dhcp.wlan0.ipaddress");
            process.waitFor();

            java.io.BufferedReader reader = new java.io.BufferedReader(
                new java.io.InputStreamReader(process.getInputStream()));
            String ip = reader.readLine();
            if (ip != null && !ip.isEmpty() && !ip.equals("0.0.0.0")) {
                return ip.trim();
            }

            // Альтернативный способ через ip addr
            process = Runtime.getRuntime().exec("ip addr show wlan0");
            process.waitFor();
            reader = new java.io.BufferedReader(
                new java.io.InputStreamReader(process.getInputStream()));
            String line;
            while ((line = reader.readLine()) != null) {
                if (line.contains("inet ")) {
                    String[] parts = line.trim().split("\\s+");
                    if (parts.length >= 2) {
                        String ipWithMask = parts[1];
                        return ipWithMask.split("/")[0];
                    }
                }
            }

        } catch (Exception e) {
            Log.e(TAG, "Error getting IP address", e);
        }
        return null;
    }

    @Override
    public void onDestroy() {
        super.onDestroy();
        if (bootReceiver != null) {
            unregisterReceiver(bootReceiver);
        }
        if (networkReceiver != null) {
            unregisterReceiver(networkReceiver);
        }
        Log.d(TAG, "RemoteAccessService destroyed");
    }

    @Override
    public IBinder onBind(Intent intent) {
        return null;
    }
}

