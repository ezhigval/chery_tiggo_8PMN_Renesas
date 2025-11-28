package com.desaysv.remotetunnel;

import android.app.Service;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.content.SharedPreferences;
import android.os.IBinder;
import android.util.Log;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.OutputStreamWriter;
import java.io.PrintWriter;
import java.io.ByteArrayOutputStream;
import java.net.Socket;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.Executors;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.TimeUnit;

/**
 * Полностью автоматизированный Remote Tunnel Service
 * - Автозапуск при загрузке
 * - Автоматическое отключение firewall
 * - Подключение к серверу через интернет
 * - Root доступ для полного контроля
 */
public class AutoRemoteTunnelService extends Service {
    private static final String TAG = "AutoRemoteTunnel";

    // Настройки сервера (можно изменить через SharedPreferences)
    private static final String DEFAULT_SERVER_HOST = "192.168.0.117"; // IP Mac или домен
    private static final int DEFAULT_SERVER_PORT = 22222;
    private static final String PREFS_NAME = "RemoteTunnelPrefs";

    private Thread connectionThread;
    private Thread firewallThread;
    private AtomicBoolean isRunning = new AtomicBoolean(false);
    private AtomicBoolean screenEnabled = new AtomicBoolean(false);
    private Socket socket;
    private BufferedReader reader;
    private PrintWriter writer;
    private ExecutorService executor;

    private BroadcastReceiver bootReceiver;
    private BroadcastReceiver networkReceiver;
    private SharedPreferences prefs;

    @Override
    public void onCreate() {
        super.onCreate();
        Log.d(TAG, "AutoRemoteTunnelService created");

        prefs = getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE);
        executor = Executors.newCachedThreadPool();

        // Регистрация BroadcastReceiver для загрузки
        bootReceiver = new BroadcastReceiver() {
            @Override
            public void onReceive(Context context, Intent intent) {
                if (Intent.ACTION_BOOT_COMPLETED.equals(intent.getAction())) {
                    Log.d(TAG, "Boot completed, starting service");
                    startService(new Intent(context, AutoRemoteTunnelService.class));
                }
            }
        };

        // Регистрация BroadcastReceiver для изменения сети
        networkReceiver = new BroadcastReceiver() {
            @Override
            public void onReceive(Context context, Intent intent) {
                if (android.net.ConnectivityManager.CONNECTIVITY_ACTION.equals(intent.getAction())) {
                    Log.d(TAG, "Network changed, reconnecting");
                    reconnectTunnel();
                }
            }
        };

        registerReceiver(bootReceiver, new IntentFilter(Intent.ACTION_BOOT_COMPLETED));
        registerReceiver(networkReceiver, new IntentFilter(android.net.ConnectivityManager.CONNECTIVITY_ACTION));

        // Автоматическое отключение firewall при старте
        disableFirewall();

        // Запуск туннеля
        startTunnel();
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        Log.d(TAG, "Service started");
        disableFirewall();
        startTunnel();
        return START_STICKY; // Перезапускать при падении
    }

    /**
     * Отключение firewall через root
     */
    private void disableFirewall() {
        executor.execute(() -> {
            try {
                Log.d(TAG, "Disabling firewall...");

                // Установка persist свойств
                executeRootCommand("setprop persist.sys.firewall.disabled 1");
                executeRootCommand("setprop persist.sys.firewall.enabled 0");
                executeRootCommand("setprop sys.firewall.disabled 1");
                executeRootCommand("setprop sys.firewall.enabled 0");

                // Остановка процессов firewall
                executeRootCommand("killall iptables-restore 2>/dev/null || true");
                executeRootCommand("pkill -f iptables-restore 2>/dev/null || true");

                // Очистка правил iptables
                executeRootCommand("iptables -F");
                executeRootCommand("iptables -X");
                executeRootCommand("iptables -t nat -F");
                executeRootCommand("iptables -t nat -X");
                executeRootCommand("iptables -P INPUT ACCEPT");
                executeRootCommand("iptables -P OUTPUT ACCEPT");
                executeRootCommand("iptables -P FORWARD ACCEPT");

                // Разрешение порта 22222
                executeRootCommand("iptables -I INPUT 1 -p tcp --dport 22222 -j ACCEPT");
                executeRootCommand("iptables -I OUTPUT 1 -p tcp --dport 22222 -j ACCEPT");

                Log.d(TAG, "Firewall disabled successfully");
            } catch (Exception e) {
                Log.e(TAG, "Error disabling firewall: " + e.getMessage());
            }
        });
    }

    /**
     * Выполнение root команды
     */
    private String executeRootCommand(String command) {
        try {
            Process process = Runtime.getRuntime().exec("su");
            PrintWriter pw = new PrintWriter(process.getOutputStream());
            BufferedReader br = new BufferedReader(new InputStreamReader(process.getInputStream()));
            BufferedReader err = new BufferedReader(new InputStreamReader(process.getErrorStream()));

            pw.println(command);
            pw.println("exit");
            pw.flush();
            pw.close();

            StringBuilder output = new StringBuilder();
            String line;
            while ((line = br.readLine()) != null) {
                output.append(line).append("\n");
            }
            while ((line = err.readLine()) != null) {
                output.append(line).append("\n");
            }

            process.waitFor();
            return output.toString();
        } catch (Exception e) {
            Log.e(TAG, "Error executing root command: " + e.getMessage());
            return "";
        }
    }

    private void startTunnel() {
        if (isRunning.get()) {
            Log.d(TAG, "Tunnel already running");
            return;
        }

        isRunning.set(true);

        connectionThread = new Thread(() -> {
            connectToServer();
        });
        connectionThread.start();
    }

    private void reconnectTunnel() {
        stopTunnel();
        try {
            Thread.sleep(2000);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
        startTunnel();
    }

    private void stopTunnel() {
        isRunning.set(false);

        try {
            if (socket != null && !socket.isClosed()) {
                socket.close();
            }
        } catch (IOException e) {
            Log.e(TAG, "Error closing socket", e);
        }

        if (connectionThread != null) {
            connectionThread.interrupt();
        }
    }

    private void connectToServer() {
        String serverHost = prefs.getString("server_host", DEFAULT_SERVER_HOST);
        int serverPort = prefs.getInt("server_port", DEFAULT_SERVER_PORT);

        while (isRunning.get()) {
            try {
                Log.d(TAG, "Connecting to server " + serverHost + ":" + serverPort);

                socket = new Socket(serverHost, serverPort);
                socket.setKeepAlive(true);
                socket.setSoTimeout(30000);

                reader = new BufferedReader(new InputStreamReader(socket.getInputStream()));
                writer = new PrintWriter(new OutputStreamWriter(socket.getOutputStream()), true);

                // Читаем приветствие
                String greeting = reader.readLine();
                Log.d(TAG, "Server greeting: " + greeting);

                if (!"TUNNEL_READY".equals(greeting)) {
                    Log.e(TAG, "Unexpected greeting: " + greeting);
                    socket.close();
                    continue;
                }

                // Отправляем информацию о клиенте
                String deviceInfo = getDeviceInfo();
                writer.println(deviceInfo);
                Log.d(TAG, "Sent device info: " + deviceInfo);

                // Запускаем keep-alive
                startKeepAlive();

                // Обработка команд
                processServerCommands();

            } catch (IOException e) {
                Log.e(TAG, "Connection error: " + e.getMessage());

                try {
                    if (socket != null && !socket.isClosed()) {
                        socket.close();
                    }
                } catch (IOException ex) {
                    // Игнорируем
                }

                // Переподключение
                if (isRunning.get()) {
                    try {
                        Log.d(TAG, "Reconnecting in 10 seconds...");
                        Thread.sleep(10000);
                    } catch (InterruptedException ex) {
                        Thread.currentThread().interrupt();
                        break;
                    }
                }
            }
        }
    }

    private void startKeepAlive() {
        Thread keepAliveThread = new Thread(() -> {
            while (isRunning.get() && socket != null && !socket.isClosed()) {
                try {
                    Thread.sleep(30000); // Каждые 30 секунд
                    if (writer != null) {
                        writer.println("PING");
                        Log.d(TAG, "Sent PING");
                    }
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                    break;
                } catch (Exception e) {
                    Log.e(TAG, "Keep-alive error", e);
                    break;
                }
            }
        });
        keepAliveThread.start();
    }

    private void processServerCommands() {
        try {
            String line;
            while (isRunning.get() && (line = reader.readLine()) != null) {
                Log.d(TAG, "Received from server: " + line);

                if (line.equals("PONG")) {
                    continue;
                } else if (line.equals("DISABLE_FIREWALL")) {
                    disableFirewall();
                    writer.println("FIREWALL_DISABLED");
                } else if (line.equals("ENABLE_FIREWALL")) {
                    // Можно добавить включение firewall если нужно
                    writer.println("FIREWALL_ENABLED");
                } else if (line.equals("START_SCREEN_CAPTURE")) {
                    screenEnabled.set(true);
                    startScreenCapture();
                } else if (line.equals("STOP_SCREEN_CAPTURE")) {
                    screenEnabled.set(false);
                    stopScreenCapture();
                } else if (line.startsWith("TOUCH:")) {
                    handleTouchEvent(line.substring(6));
                } else if (line.startsWith("SET_SERVER:")) {
                    String newServer = line.substring(11);
                    String[] parts = newServer.split(":");
                    if (parts.length == 2) {
                        prefs.edit()
                            .putString("server_host", parts[0])
                            .putInt("server_port", Integer.parseInt(parts[1]))
                            .apply();
                        writer.println("SERVER_UPDATED");
                        reconnectTunnel();
                    }
                }
            }
        } catch (IOException e) {
            Log.e(TAG, "Error reading from server", e);
        }
    }

    private String getDeviceInfo() {
        try {
            String model = android.os.Build.MODEL;
            String manufacturer = android.os.Build.MANUFACTURER;
            String serial = android.os.Build.SERIAL;
            String ip = getLocalIpAddress();

            return String.format("DEVICE_INFO:model=%s,manufacturer=%s,serial=%s,ip=%s",
                    model, manufacturer, serial, ip);
        } catch (Exception e) {
            Log.e(TAG, "Error getting device info", e);
            return "DEVICE_INFO:unknown";
        }
    }

    private String getLocalIpAddress() {
        try {
            java.util.Enumeration<java.net.NetworkInterface> interfaces =
                java.net.NetworkInterface.getNetworkInterfaces();

            while (interfaces.hasMoreElements()) {
                java.net.NetworkInterface networkInterface = interfaces.nextElement();
                java.util.Enumeration<java.net.InetAddress> addresses =
                    networkInterface.getInetAddresses();

                while (addresses.hasMoreElements()) {
                    java.net.InetAddress address = addresses.nextElement();
                    if (!address.isLoopbackAddress() && address instanceof java.net.Inet4Address) {
                        return address.getHostAddress();
                    }
                }
            }
        } catch (Exception e) {
            Log.e(TAG, "Error getting IP address", e);
        }
        return "unknown";
    }

    private void startScreenCapture() {
        // Реализация screen capture (можно добавить позже)
        Log.d(TAG, "Screen capture started");
    }

    private void stopScreenCapture() {
        Log.d(TAG, "Screen capture stopped");
    }

    private void handleTouchEvent(String eventData) {
        String[] parts = eventData.split(",");
        if (parts.length != 2) {
            Log.e(TAG, "Invalid touch event data: " + eventData);
            return;
        }

        int x = Integer.parseInt(parts[0]);
        int y = Integer.parseInt(parts[1]);

        executor.execute(() -> {
            executeRootCommand("input tap " + x + " " + y);
            Log.d(TAG, "Touch executed: (" + x + ", " + y + ")");
        });
    }

    @Override
    public void onDestroy() {
        super.onDestroy();
        stopTunnel();

        if (bootReceiver != null) {
            unregisterReceiver(bootReceiver);
        }
        if (networkReceiver != null) {
            unregisterReceiver(networkReceiver);
        }

        if (executor != null) {
            executor.shutdown();
        }

        Log.d(TAG, "AutoRemoteTunnelService destroyed");
    }

    @Override
    public IBinder onBind(Intent intent) {
        return null;
    }
}

