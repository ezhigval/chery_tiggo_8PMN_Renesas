package com.desaysv.remotetunnel;

import android.app.Service;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
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

/**
 * Reverse Tunnel Client для ГУ
 * Подключается к Mac серверу через интернет и устанавливает туннель
 */
public class ReverseTunnelClient extends Service {
    private static final String TAG = "ReverseTunnelClient";

    // Настройки сервера (можно вынести в SharedPreferences)
    private static final String SERVER_HOST = "your-mac-ip-or-domain.com"; // Заменить на IP или домен Mac
    private static final int SERVER_PORT = 22222;

    private Thread connectionThread;
    private Thread screenshotThread;
    private AtomicBoolean isRunning = new AtomicBoolean(false);
    private AtomicBoolean screenEnabled = new AtomicBoolean(false);
    private Socket socket;
    private BufferedReader reader;
    private PrintWriter writer;

    private BroadcastReceiver bootReceiver;
    private BroadcastReceiver networkReceiver;

    @Override
    public void onCreate() {
        super.onCreate();
        Log.d(TAG, "ReverseTunnelClient created");

        // Регистрация BroadcastReceiver для загрузки
        bootReceiver = new BroadcastReceiver() {
            @Override
            public void onReceive(Context context, Intent intent) {
                if (Intent.ACTION_BOOT_COMPLETED.equals(intent.getAction())) {
                    Log.d(TAG, "Boot completed, starting reverse tunnel");
                    startTunnel();
                }
            }
        };

        // Регистрация BroadcastReceiver для изменения сети
        networkReceiver = new BroadcastReceiver() {
            @Override
            public void onReceive(Context context, Intent intent) {
                if (android.net.ConnectivityManager.CONNECTIVITY_ACTION.equals(intent.getAction())) {
                    Log.d(TAG, "Network changed, reconnecting tunnel");
                    reconnectTunnel();
                }
            }
        };

        registerReceiver(bootReceiver, new IntentFilter(Intent.ACTION_BOOT_COMPLETED));
        registerReceiver(networkReceiver, new IntentFilter(android.net.ConnectivityManager.CONNECTIVITY_ACTION));

        // Запуск туннеля сразу
        startTunnel();
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        Log.d(TAG, "Service started");
        startTunnel();
        return START_STICKY; // Перезапускать при падении
    }

    private void startTunnel() {
        if (isRunning.get()) {
            Log.d(TAG, "Tunnel already running");
            return;
        }

        isRunning.set(true);

        connectionThread = new Thread(new Runnable() {
            @Override
            public void run() {
                connectToServer();
            }
        });
        connectionThread.start();
    }

    private void reconnectTunnel() {
        stopTunnel();
        try {
            Thread.sleep(2000); // Пауза перед переподключением
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
        while (isRunning.get()) {
            try {
                Log.d(TAG, "Connecting to server " + SERVER_HOST + ":" + SERVER_PORT);

                // Подключение к серверу
                socket = new Socket(SERVER_HOST, SERVER_PORT);
                socket.setKeepAlive(true);
                socket.setSoTimeout(30000); // 30 секунд таймаут

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

                // Запускаем keep-alive и обработку команд
                startKeepAlive();
                startScreenshotCapture();
                processServerCommands();

            } catch (IOException e) {
                Log.e(TAG, "Connection error: " + e.getMessage());

                // Закрываем соединение
                try {
                    if (socket != null && !socket.isClosed()) {
                        socket.close();
                    }
                } catch (IOException ex) {
                    // Игнорируем
                }

                // Ждем перед переподключением
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
        Thread keepAliveThread = new Thread(new Runnable() {
            @Override
            public void run() {
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
                    // Ответ на PING
                    continue;
                }

                if (line.startsWith("SCREEN:")) {
                    // Команда включения/выключения экрана
                    String mode = line.substring(7);
                    screenEnabled.set("ON".equals(mode));
                    Log.d(TAG, "Screen mode: " + mode);
                }

                if (line.equals("REQUEST_SCREENSHOT")) {
                    // Запрос скриншота
                    sendScreenshot();
                }

                if (line.startsWith("TOUCH:")) {
                    // Touch событие от сервера
                    String[] coords = line.substring(6).split(",");
                    if (coords.length == 2) {
                        int x = Integer.parseInt(coords[0]);
                        int y = Integer.parseInt(coords[1]);
                        executeTouch(x, y);
                    }
                }

                if (line.startsWith("TOUCH_MOVE:")) {
                    // Touch move событие
                    String[] coords = line.substring(11).split(",");
                    if (coords.length == 2) {
                        int x = Integer.parseInt(coords[0]);
                        int y = Integer.parseInt(coords[1]);
                        executeTouchMove(x, y);
                    }
                }

                if (line.equals("TOUCH_UP")) {
                    // Touch up событие
                    executeTouchUp();
                }
            }
        } catch (IOException e) {
            Log.e(TAG, "Error reading from server", e);
        }
    }

    private void startScreenshotCapture() {
        screenshotThread = new Thread(new Runnable() {
            @Override
            public void run() {
                while (isRunning.get()) {
                    if (screenEnabled.get() && writer != null) {
                        try {
                            sendScreenshot();
                            Thread.sleep(500); // 2 FPS для экономии трафика
                        } catch (InterruptedException e) {
                            Thread.currentThread().interrupt();
                            break;
                        } catch (Exception e) {
                            Log.e(TAG, "Error capturing screenshot", e);
                        }
                    } else {
                        try {
                            Thread.sleep(1000);
                        } catch (InterruptedException e) {
                            Thread.currentThread().interrupt();
                            break;
                        }
                    }
                }
            }
        });
        screenshotThread.start();
    }

    private void sendScreenshot() {
        try {
            // Делаем скриншот через screencap
            Process process = Runtime.getRuntime().exec("screencap -p");
            java.io.InputStream inputStream = process.getInputStream();

            // Читаем изображение
            java.io.ByteArrayOutputStream outputStream = new java.io.ByteArrayOutputStream();
            byte[] buffer = new byte[4096];
            int bytesRead;
            while ((bytesRead = inputStream.read(buffer)) != -1) {
                outputStream.write(buffer, 0, bytesRead);
            }

            byte[] imageBytes = outputStream.toByteArray();

            // Оптимизация: сжатие JPEG для экономии трафика
            try {
                Bitmap bitmap = BitmapFactory.decodeByteArray(imageBytes, 0, imageBytes.length);
                if (bitmap != null) {
                    // Масштабирование (опционально, для экономии трафика)
                    int scale = 1; // Можно изменить на 2 для уменьшения в 2 раза
                    if (scale > 1) {
                        Bitmap scaled = Bitmap.createScaledBitmap(
                            bitmap,
                            bitmap.getWidth() / scale,
                            bitmap.getHeight() / scale,
                            true
                        );
                        bitmap.recycle();
                        bitmap = scaled;
                    }

                    // Сжатие JPEG
                    ByteArrayOutputStream jpegStream = new ByteArrayOutputStream();
                    bitmap.compress(Bitmap.CompressFormat.JPEG, 70, jpegStream);
                    imageBytes = jpegStream.toByteArray();
                    bitmap.recycle();
                }
            } catch (Exception e) {
                Log.w(TAG, "Error compressing screenshot, using original", e);
            }

            // Кодируем в base64
            String base64Image = android.util.Base64.encodeToString(
                imageBytes,
                android.util.Base64.NO_WRAP
            );

            // Отправляем на сервер
            if (writer != null) {
                writer.println("SCREENSHOT:" + base64Image);
                writer.flush();
            }

        } catch (Exception e) {
            Log.e(TAG, "Error sending screenshot", e);
        }
    }

    private void executeTouch(int x, int y) {
        try {
            // Выполняем touch через input tap
            String command = String.format("input tap %d %d", x, y);
            Runtime.getRuntime().exec(command);
            Log.d(TAG, "Touch executed: (" + x + ", " + y + ")");
        } catch (Exception e) {
            Log.e(TAG, "Error executing touch", e);
        }
    }

    private void executeTouchMove(int x, int y) {
        try {
            // Touch move через input swipe (с небольшой задержкой)
            String command = String.format("input swipe %d %d %d %d 10", x, y, x, y);
            Runtime.getRuntime().exec(command);
        } catch (Exception e) {
            Log.e(TAG, "Error executing touch move", e);
        }
    }

    private void executeTouchUp() {
        try {
            // Touch up (отпускание)
            // В Android это обычно не требуется, но можно добавить
            Log.d(TAG, "Touch up executed");
        } catch (Exception e) {
            Log.e(TAG, "Error executing touch up", e);
        }
    }

    private String getDeviceInfo() {
        try {
            // Получаем информацию об устройстве
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

        Log.d(TAG, "ReverseTunnelClient destroyed");
    }

    @Override
    public IBinder onBind(Intent intent) {
        return null;
    }
}

