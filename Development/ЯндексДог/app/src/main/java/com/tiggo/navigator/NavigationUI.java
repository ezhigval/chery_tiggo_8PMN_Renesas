/**
 * NavigationUI - UI компоненты для отображения навигации в стиле Яндекс Навигатора
 * 
 * Отображает интерфейс точно как на скриншоте:
 * - Верхняя панель с кнопками поиска, переориентации и "Сбросить"
 * - Основной блок навигации (верхний левый) - синий прямоугольник с инструкцией
 * - Нижняя панель с информацией о маршруте (время прибытия, время, расстояние)
 * - Правые кнопки управления (настройки, камера, зум)
 */
package com.tiggo.navigator;

import android.content.Context;
import android.content.res.Resources;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.Path;
import android.graphics.RectF;
import android.graphics.Typeface;
import android.util.AttributeSet;
import android.view.MotionEvent;
import android.view.View;

/**
 * View для отображения навигационного интерфейса поверх OpenGL
 * Дизайн точно как в Яндекс Навигаторе
 */
public class NavigationUI extends View {
    private static final String TAG = "NavigationUI";
    
    // Состояние навигации
    private boolean mNavigationActive = false; // Активна ли навигация (следование маршруту)
    
    // Данные навигации
    private int mNextManeuverType = 0; // Тип маневра (0=нет, 1=налево, 2=направо, 3=разворот, 4=прямо)
    private int mNextManeuverDistance = 0; // Расстояние до маневра в метрах
    private String mNextManeuverStreet = ""; // Название улицы для маневра
    private String mArrivalTime = ""; // Время прибытия (например, "21:53")
    private int mRemainingTimeMinutes = 0; // Оставшееся время в минутах
    private float mRemainingDistanceKm = 0.0f; // Оставшееся расстояние в км
    
    // Избранные места (для режима без маршрута)
    private String[] mFavoritePlaces = new String[0]; // Массив названий избранных мест
    private int[] mFavoriteTimes = new int[0]; // Массив времени до избранных мест (минуты)
    
    // Кисти для рисования
    private Paint mTextPaint;
    private Paint mIconPaint;
    private Paint mButtonBgPaint;
    private Paint mNavigationBoxPaint;
    private Paint mInfoBoxPaint;
    
    // Кнопки (режим навигации)
    private RectF mSearchButtonRect;
    private RectF mOrientationButtonRect;
    private RectF mResetButtonRect;
    private RectF mSettingsButtonRect;
    private RectF mCameraButtonRect;
    private RectF mZoomInButtonRect;
    private RectF mZoomOutButtonRect;
    
    // Кнопки (режим без маршрута)
    private RectF mChatButtonRect; // Иконка чата (верхний левый)
    private RectF mMenuButtonRect; // Меню (правый сайдбар, вверху)
    private RectF mBookmarkButtonRect; // Закладка (правый сайдбар)
    private RectF mZoomInSidebarRect; // Зум + (правый сайдбар)
    private RectF mZoomOutSidebarRect; // Зум - (правый сайдбар)
    private RectF mCenterButtonRect; // Центрирование (синяя стрелка вверх)
    private RectF mSearchSidebarRect; // Поиск (правый сайдбар, внизу)
    
    // Размеры и отступы
    private float mDp; // Density pixel для масштабирования
    
    // Цвета (как в Яндекс Навигаторе)
    private static final int COLOR_LIGHT_BLUE = 0xFF4FC3F7; // Светло-голубой для иконок и текста
    private static final int COLOR_NAVIGATION_BOX = 0xFF1E88E5; // Синий для блока навигации
    private static final int COLOR_BUTTON_BG = 0xCC000000; // Темный фон для кнопок
    
    public NavigationUI(Context context) {
        super(context);
        init();
    }
    
    public NavigationUI(Context context, AttributeSet attrs) {
        super(context, attrs);
        init();
    }
    
    public NavigationUI(Context context, AttributeSet attrs, int defStyleAttr) {
        super(context, attrs, defStyleAttr);
        init();
    }
    
    private void init() {
        Resources res = getResources();
        mDp = res.getDisplayMetrics().density * 3.0f; // Увеличиваем размер на 200% (в 3 раза)
        
        // Основной текст (белый)
        mTextPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
        mTextPaint.setColor(Color.WHITE);
        mTextPaint.setTypeface(Typeface.create(Typeface.DEFAULT, Typeface.NORMAL));
        
        // Иконки и светлый текст (светло-голубой)
        mIconPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
        mIconPaint.setColor(COLOR_LIGHT_BLUE);
        mIconPaint.setStyle(Paint.Style.STROKE);
        mIconPaint.setStrokeWidth(3 * mDp);
        mIconPaint.setStrokeCap(Paint.Cap.ROUND);
        mIconPaint.setStrokeJoin(Paint.Join.ROUND);
        
        // Фон для кнопок (темный)
        mButtonBgPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
        mButtonBgPaint.setColor(COLOR_BUTTON_BG);
        mButtonBgPaint.setStyle(Paint.Style.FILL);
        
        // Фон для блока навигации (синий)
        mNavigationBoxPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
        mNavigationBoxPaint.setColor(COLOR_NAVIGATION_BOX);
        mNavigationBoxPaint.setStyle(Paint.Style.FILL);
        
        // Фон для информационной панели (черный)
        mInfoBoxPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
        mInfoBoxPaint.setColor(0xFF000000);
        mInfoBoxPaint.setStyle(Paint.Style.FILL);
        
        // Инициализируем прямоугольники кнопок (режим навигации)
        mSearchButtonRect = new RectF();
        mOrientationButtonRect = new RectF();
        mResetButtonRect = new RectF();
        mSettingsButtonRect = new RectF();
        mCameraButtonRect = new RectF();
        mZoomInButtonRect = new RectF();
        mZoomOutButtonRect = new RectF();
        
        // Инициализируем прямоугольники кнопок (режим без маршрута)
        mChatButtonRect = new RectF();
        mMenuButtonRect = new RectF();
        mBookmarkButtonRect = new RectF();
        mZoomInSidebarRect = new RectF();
        mZoomOutSidebarRect = new RectF();
        mCenterButtonRect = new RectF();
        mSearchSidebarRect = new RectF();
        
        // Прозрачный фон
        setBackgroundColor(Color.TRANSPARENT);
        
        // Включаем аппаратное ускорение
        setLayerType(View.LAYER_TYPE_HARDWARE, null);
    }
    
    /**
     * Установка состояния навигации (активна/неактивна)
     */
    public void setNavigationActive(boolean active) {
        mNavigationActive = active;
        invalidate();
    }
    
    /**
     * Обновление следующего маневра
     */
    public void updateNextManeuver(int type, int distance, String streetName) {
        mNextManeuverType = type;
        mNextManeuverDistance = distance;
        mNextManeuverStreet = streetName != null ? streetName : "";
        // Если есть маневр, значит навигация активна
        if (type > 0) {
            mNavigationActive = true;
        }
        invalidate();
    }
    
    /**
     * Обновление информации о маршруте
     */
    public void updateRouteInfo(String arrivalTime, int remainingTimeMinutes, float remainingDistanceKm) {
        mArrivalTime = arrivalTime != null ? arrivalTime : "";
        mRemainingTimeMinutes = remainingTimeMinutes;
        mRemainingDistanceKm = remainingDistanceKm;
        // Если есть информация о маршруте, значит навигация активна
        if (remainingTimeMinutes > 0 || remainingDistanceKm > 0) {
            mNavigationActive = true;
        }
        invalidate();
    }
    
    /**
     * Обновление избранных мест (для режима без маршрута)
     */
    public void updateFavoritePlaces(String[] places, int[] times) {
        if (places != null && times != null && places.length == times.length) {
            mFavoritePlaces = places;
            mFavoriteTimes = times;
            invalidate();
        }
    }
    
    @Override
    protected void onDraw(Canvas canvas) {
        super.onDraw(canvas);
        
        int width = getWidth();
        int height = getHeight();
        
        if (width == 0 || height == 0) {
            return;
        }
        
        float padding = 16 * mDp;
        float topPadding = 8 * mDp;
        
        if (mNavigationActive) {
            // ========== РЕЖИМ С МАРШРУТОМ (навигация активна) ==========
            // 1. Верхняя панель
            drawTopBar(canvas, width, padding, topPadding);
            
            // 2. Основной блок навигации (верхний левый)
            if (mNextManeuverType > 0) {
                drawNavigationBox(canvas, width, padding, topPadding);
            }
            
            // 3. Нижняя информационная панель (левый нижний угол)
            if (!mArrivalTime.isEmpty() || mRemainingTimeMinutes > 0 || mRemainingDistanceKm > 0) {
                drawInfoBox(canvas, width, height, padding);
            }
            
            // 4. Правые кнопки управления
            drawRightButtons(canvas, width, height, padding);
        } else {
            // ========== РЕЖИМ БЕЗ МАРШРУТА ==========
            // 1. Иконка чата (верхний левый)
            drawChatButton(canvas, width, padding, topPadding);
            
            // 2. Правый сайдбар с кнопками
            drawRightSidebar(canvas, width, height, padding);
            
            // 3. Нижняя панель с избранными местами
            if (mFavoritePlaces.length > 0) {
                drawFavoritePlacesBar(canvas, width, height, padding);
            }
        }
    }
    
    /**
     * Рисование верхней панели
     */
    private void drawTopBar(Canvas canvas, int width, float padding, float topPadding) {
        float iconSize = 24 * mDp;
        float buttonSize = 48 * mDp;
        float y = topPadding + buttonSize / 2;
        
        // Кнопка поиска (слева)
        float searchX = padding;
        mSearchButtonRect.set(searchX, topPadding, searchX + buttonSize, topPadding + buttonSize);
        drawSearchIcon(canvas, searchX + buttonSize / 2, y, iconSize);
        
        // Кнопка переориентации (слева, рядом с поиском)
        float orientationX = searchX + buttonSize + 8 * mDp;
        mOrientationButtonRect.set(orientationX, topPadding, orientationX + buttonSize, topPadding + buttonSize);
        drawOrientationIcon(canvas, orientationX + buttonSize / 2, y, iconSize);
        
        // Кнопка "Сбросить" (справа)
        mTextPaint.setTextSize(16 * mDp);
        mTextPaint.setColor(COLOR_LIGHT_BLUE);
        String resetText = "Сбросить";
        float resetTextWidth = mTextPaint.measureText(resetText);
        float resetX = width - padding - resetTextWidth;
        mResetButtonRect.set(resetX - 8 * mDp, topPadding, width - padding, topPadding + buttonSize);
        canvas.drawText(resetText, resetX, y + 6 * mDp, mTextPaint);
    }
    
    /**
     * Рисование основного блока навигации (синий прямоугольник)
     */
    private void drawNavigationBox(Canvas canvas, int width, float padding, float topPadding) {
        float boxWidth = 280 * mDp;
        float boxHeight = 120 * mDp;
        float boxX = padding;
        float boxY = topPadding + 60 * mDp;
        
        RectF boxRect = new RectF(boxX, boxY, boxX + boxWidth, boxY + boxHeight);
        float cornerRadius = 12 * mDp;
        canvas.drawRoundRect(boxRect, cornerRadius, cornerRadius, mNavigationBoxPaint);
        
        // Стрелка маневра (белая)
        float arrowX = boxX + 24 * mDp;
        float arrowY = boxY + boxHeight / 2;
        float arrowSize = 48 * mDp;
        drawManeuverArrow(canvas, arrowX, arrowY, mNextManeuverType, Color.WHITE, arrowSize);
        
        // Расстояние до маневра
        mTextPaint.setTextSize(20 * mDp);
        mTextPaint.setColor(Color.WHITE);
        mTextPaint.setTypeface(Typeface.create(Typeface.DEFAULT, Typeface.BOLD));
        String distanceText = formatDistance(mNextManeuverDistance);
        float distanceX = arrowX + arrowSize + 16 * mDp;
        float distanceY = arrowY - 8 * mDp;
        canvas.drawText(distanceText, distanceX, distanceY, mTextPaint);
        
        // Название улицы
        mTextPaint.setTextSize(16 * mDp);
        mTextPaint.setTypeface(Typeface.create(Typeface.DEFAULT, Typeface.NORMAL));
        String streetText = mNextManeuverStreet.isEmpty() ? "" : mNextManeuverStreet;
        if (!streetText.isEmpty() && mTextPaint.measureText(streetText) > boxWidth - distanceX - 16 * mDp) {
            streetText = truncateText(mTextPaint, streetText, boxWidth - distanceX - 16 * mDp);
        }
        float streetY = arrowY + 20 * mDp;
        canvas.drawText(streetText, distanceX, streetY, mTextPaint);
        
        // Иконки полос (внизу блока)
        float lanesY = boxY + boxHeight - 20 * mDp;
        float lanesX = distanceX;
        drawLaneGuidance(canvas, lanesX, lanesY, mNextManeuverType);
    }
    
    /**
     * Рисование нижней информационной панели
     */
    private void drawInfoBox(Canvas canvas, int width, int height, float padding) {
        float boxWidth = 200 * mDp;
        float boxHeight = 80 * mDp;
        float boxX = padding;
        float boxY = height - padding - boxHeight;
        
        RectF boxRect = new RectF(boxX, boxY, boxX + boxWidth, boxY + boxHeight);
        float cornerRadius = 8 * mDp;
        canvas.drawRoundRect(boxRect, cornerRadius, cornerRadius, mInfoBoxPaint);
        
        float textX = boxX + 12 * mDp;
        float lineHeight = 24 * mDp;
        
        // Время прибытия
        if (!mArrivalTime.isEmpty()) {
            mTextPaint.setTextSize(14 * mDp);
            mTextPaint.setColor(Color.WHITE);
            mTextPaint.setTypeface(Typeface.create(Typeface.DEFAULT, Typeface.NORMAL));
            String arrivalText = mArrivalTime + " прибытие";
            canvas.drawText(arrivalText, textX, boxY + 20 * mDp, mTextPaint);
        }
        
        // Оставшееся время
        if (mRemainingTimeMinutes > 0) {
            mTextPaint.setTextSize(16 * mDp);
            mTextPaint.setTypeface(Typeface.create(Typeface.DEFAULT, Typeface.BOLD));
            String timeText = mRemainingTimeMinutes + " мин";
            canvas.drawText(timeText, textX, boxY + 20 * mDp + lineHeight, mTextPaint);
        }
        
        // Оставшееся расстояние
        if (mRemainingDistanceKm > 0) {
            mTextPaint.setTextSize(16 * mDp);
            String distanceText = String.format("%.1f км", mRemainingDistanceKm);
            canvas.drawText(distanceText, textX, boxY + 20 * mDp + lineHeight * 2, mTextPaint);
        }
    }
    
    /**
     * Рисование правых кнопок управления
     */
    private void drawRightButtons(Canvas canvas, int width, int height, float padding) {
        float buttonSize = 48 * mDp;
        float buttonMargin = 8 * mDp;
        float rightX = width - padding - buttonSize;
        
        // Кнопка настроек (вверху)
        float settingsY = padding;
        mSettingsButtonRect.set(rightX, settingsY, rightX + buttonSize, settingsY + buttonSize);
        canvas.drawRoundRect(mSettingsButtonRect, 8 * mDp, 8 * mDp, mButtonBgPaint);
        drawSettingsIcon(canvas, rightX + buttonSize / 2, settingsY + buttonSize / 2, 20 * mDp);
        
        // Кнопка камеры/вида (ниже настроек)
        float cameraY = settingsY + buttonSize + buttonMargin;
        mCameraButtonRect.set(rightX, cameraY, rightX + buttonSize, cameraY + buttonSize);
        canvas.drawRoundRect(mCameraButtonRect, 8 * mDp, 8 * mDp, mButtonBgPaint);
        drawCameraIcon(canvas, rightX + buttonSize / 2, cameraY + buttonSize / 2, 20 * mDp);
        
        // Кнопки зума (внизу)
        float zoomY = height - padding - buttonSize * 2 - buttonMargin;
        mZoomInButtonRect.set(rightX, zoomY, rightX + buttonSize, zoomY + buttonSize);
        canvas.drawRoundRect(mZoomInButtonRect, 8 * mDp, 8 * mDp, mButtonBgPaint);
        drawZoomIcon(canvas, rightX + buttonSize / 2, zoomY + buttonSize / 2, 20 * mDp, true);
        
        float zoomOutY = zoomY + buttonSize + buttonMargin;
        mZoomOutButtonRect.set(rightX, zoomOutY, rightX + buttonSize, zoomOutY + buttonSize);
        canvas.drawRoundRect(mZoomOutButtonRect, 8 * mDp, 8 * mDp, mButtonBgPaint);
        drawZoomIcon(canvas, rightX + buttonSize / 2, zoomOutY + buttonSize / 2, 20 * mDp, false);
    }
    
    /**
     * Рисование иконки поиска (лупа)
     */
    private void drawSearchIcon(Canvas canvas, float centerX, float centerY, float size) {
        Paint iconPaint = new Paint(mIconPaint);
        iconPaint.setColor(COLOR_LIGHT_BLUE);
        iconPaint.setStyle(Paint.Style.STROKE);
        iconPaint.setStrokeWidth(3 * mDp);
        
        // Круг лупы
        float radius = size * 0.35f;
        canvas.drawCircle(centerX, centerY, radius, iconPaint);
        
        // Ручка лупы
        float handleX = centerX + radius * 0.7f;
        float handleY = centerY + radius * 0.7f;
        canvas.drawLine(handleX, handleY, handleX + radius * 0.5f, handleY + radius * 0.5f, iconPaint);
    }
    
    /**
     * Рисование иконки переориентации (две стрелки)
     */
    private void drawOrientationIcon(Canvas canvas, float centerX, float centerY, float size) {
        Paint iconPaint = new Paint(mIconPaint);
        iconPaint.setColor(COLOR_LIGHT_BLUE);
        iconPaint.setStyle(Paint.Style.STROKE);
        iconPaint.setStrokeWidth(3 * mDp);
        
        float halfSize = size * 0.4f;
        
        // Две стрелки, переплетенные
        Path path = new Path();
        // Первая стрелка (↖)
        path.moveTo(centerX - halfSize, centerY - halfSize);
        path.lineTo(centerX, centerY);
        path.lineTo(centerX - halfSize * 0.5f, centerY - halfSize * 0.5f);
        // Вторая стрелка (↘)
        path.moveTo(centerX + halfSize, centerY + halfSize);
        path.lineTo(centerX, centerY);
        path.lineTo(centerX + halfSize * 0.5f, centerY + halfSize * 0.5f);
        
        canvas.drawPath(path, iconPaint);
    }
    
    /**
     * Рисование иконки настроек (шестеренка)
     */
    private void drawSettingsIcon(Canvas canvas, float centerX, float centerY, float size) {
        Paint iconPaint = new Paint(mTextPaint);
        iconPaint.setColor(Color.WHITE);
        iconPaint.setStyle(Paint.Style.STROKE);
        iconPaint.setStrokeWidth(2.5f * mDp);
        
        float radius = size * 0.4f;
        float angleStep = (float)(2 * Math.PI / 8);
        
        // Рисуем шестеренку
        Path path = new Path();
        for (int i = 0; i < 8; i++) {
            float angle = (float)(i * angleStep);
            float outerRadius = radius * 1.2f;
            float innerRadius = radius * 0.8f;
            
            float x1 = centerX + (float)Math.cos(angle) * outerRadius;
            float y1 = centerY + (float)Math.sin(angle) * outerRadius;
            float x2 = centerX + (float)Math.cos(angle) * innerRadius;
            float y2 = centerY + (float)Math.sin(angle) * innerRadius;
            
            if (i == 0) {
                path.moveTo(x1, y1);
            } else {
                path.lineTo(x1, y1);
            }
            path.lineTo(x2, y2);
        }
        path.close();
        
        canvas.drawPath(path, iconPaint);
        canvas.drawCircle(centerX, centerY, radius * 0.3f, iconPaint);
    }
    
    /**
     * Рисование иконки камеры/вида
     */
    private void drawCameraIcon(Canvas canvas, float centerX, float centerY, float size) {
        Paint iconPaint = new Paint(mTextPaint);
        iconPaint.setColor(Color.WHITE);
        iconPaint.setStyle(Paint.Style.STROKE);
        iconPaint.setStrokeWidth(2.5f * mDp);
        
        float halfSize = size * 0.4f;
        
        // Круг с стрелками наружу
        canvas.drawCircle(centerX, centerY, halfSize, iconPaint);
        
        // Стрелки наружу
        float arrowLength = halfSize * 0.6f;
        // Вверх
        canvas.drawLine(centerX, centerY - halfSize, centerX, centerY - halfSize - arrowLength * 0.3f, iconPaint);
        // Вниз
        canvas.drawLine(centerX, centerY + halfSize, centerX, centerY + halfSize + arrowLength * 0.3f, iconPaint);
        // Влево
        canvas.drawLine(centerX - halfSize, centerY, centerX - halfSize - arrowLength * 0.3f, centerY, iconPaint);
        // Вправо
        canvas.drawLine(centerX + halfSize, centerY, centerX + halfSize + arrowLength * 0.3f, centerY, iconPaint);
    }
    
    /**
     * Рисование иконки зума
     */
    private void drawZoomIcon(Canvas canvas, float centerX, float centerY, float size, boolean zoomIn) {
        Paint iconPaint = new Paint(mTextPaint);
        iconPaint.setColor(Color.WHITE);
        iconPaint.setStyle(Paint.Style.STROKE);
        iconPaint.setStrokeWidth(3 * mDp);
        iconPaint.setStrokeCap(Paint.Cap.ROUND);
        
        float halfSize = size * 0.3f;
        
        // Круг
        canvas.drawCircle(centerX, centerY, halfSize, iconPaint);
        
        // Горизонтальная линия
        canvas.drawLine(centerX - halfSize * 0.5f, centerY, centerX + halfSize * 0.5f, centerY, iconPaint);
        
        // Вертикальная линия (только для зума +)
        if (zoomIn) {
            canvas.drawLine(centerX, centerY - halfSize * 0.5f, centerX, centerY + halfSize * 0.5f, iconPaint);
        }
    }
    
    /**
     * Рисование стрелки маневра
     */
    private void drawManeuverArrow(Canvas canvas, float centerX, float centerY, int type, int color, float size) {
        Paint arrowPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
        arrowPaint.setColor(color);
        arrowPaint.setStyle(Paint.Style.FILL);
        
        Path arrowPath = new Path();
        float halfSize = size / 2;
        
        switch (type) {
            case 1: // Налево ←
                arrowPath.moveTo(centerX + halfSize * 0.4f, centerY);
                arrowPath.lineTo(centerX - halfSize * 0.2f, centerY - halfSize * 0.6f);
                arrowPath.lineTo(centerX - halfSize * 0.2f, centerY + halfSize * 0.6f);
                arrowPath.close();
                break;
            case 2: // Направо →
                arrowPath.moveTo(centerX - halfSize * 0.4f, centerY);
                arrowPath.lineTo(centerX + halfSize * 0.2f, centerY - halfSize * 0.6f);
                arrowPath.lineTo(centerX + halfSize * 0.2f, centerY + halfSize * 0.6f);
                arrowPath.close();
                break;
            case 3: // Разворот ↻
                RectF arcRect = new RectF(
                    centerX - halfSize * 0.8f, centerY - halfSize * 0.8f,
                    centerX + halfSize * 0.8f, centerY + halfSize * 0.8f
                );
                arrowPaint.setStyle(Paint.Style.STROKE);
                arrowPaint.setStrokeWidth(4 * mDp);
                canvas.drawArc(arcRect, 90, 270, false, arrowPaint);
                arrowPaint.setStyle(Paint.Style.FILL);
                arrowPath.moveTo(centerX - halfSize * 0.4f, centerY - halfSize * 0.8f);
                arrowPath.lineTo(centerX - halfSize * 0.2f, centerY - halfSize * 1.0f);
                arrowPath.lineTo(centerX + halfSize * 0.1f, centerY - halfSize * 0.8f);
                arrowPath.close();
                break;
            case 4: // Прямо ↑
            default:
                arrowPath.moveTo(centerX, centerY - halfSize * 0.4f);
                arrowPath.lineTo(centerX - halfSize * 0.6f, centerY + halfSize * 0.4f);
                arrowPath.lineTo(centerX + halfSize * 0.6f, centerY + halfSize * 0.4f);
                arrowPath.close();
                break;
        }
        
        canvas.drawPath(arrowPath, arrowPaint);
    }
    
    /**
     * Рисование иконок полос
     */
    private void drawLaneGuidance(Canvas canvas, float x, float y, int maneuverType) {
        Paint lanePaint = new Paint(Paint.ANTI_ALIAS_FLAG);
        lanePaint.setColor(Color.WHITE);
        lanePaint.setStyle(Paint.Style.FILL);
        lanePaint.setStrokeWidth(2 * mDp);
        
        float laneSize = 16 * mDp;
        float laneSpacing = 4 * mDp;
        
        // Рисуем иконки полос в зависимости от типа маневра
        // Для поворота направо: прямо и направо
        if (maneuverType == 2) {
            // Прямо (серая/неактивная)
            lanePaint.setColor(0x80FFFFFF);
            drawLaneArrow(canvas, x, y, laneSize, 4);
            // Направо (белая/активная)
            lanePaint.setColor(Color.WHITE);
            drawLaneArrow(canvas, x + laneSize + laneSpacing, y, laneSize, 2);
        } else {
            // По умолчанию показываем только активную полосу
            drawLaneArrow(canvas, x, y, laneSize, maneuverType);
        }
    }
    
    /**
     * Рисование иконки полосы (маленькая стрелка)
     */
    private void drawLaneArrow(Canvas canvas, float x, float y, float size, int direction) {
        Paint arrowPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
        arrowPaint.setColor(Color.WHITE);
        arrowPaint.setStyle(Paint.Style.FILL);
        
        Path path = new Path();
        float halfSize = size / 2;
        
        switch (direction) {
            case 2: // Направо
                path.moveTo(x, y);
                path.lineTo(x + halfSize, y - halfSize * 0.5f);
                path.lineTo(x + halfSize, y + halfSize * 0.5f);
                path.close();
                break;
            case 1: // Налево
                path.moveTo(x + size, y);
                path.lineTo(x + halfSize, y - halfSize * 0.5f);
                path.lineTo(x + halfSize, y + halfSize * 0.5f);
                path.close();
                break;
            case 4: // Прямо
            default:
                path.moveTo(x + halfSize, y - halfSize);
                path.lineTo(x, y);
                path.lineTo(x + size, y);
                path.close();
                break;
        }
        
        canvas.drawPath(path, arrowPaint);
    }
    
    /**
     * Форматирование расстояния
     */
    private String formatDistance(int meters) {
        if (meters >= 1000) {
            return String.format("%.1f км", meters / 1000.0f);
        } else {
            return String.format("%d м", meters);
        }
    }
    
    /**
     * Обрезание текста
     */
    private String truncateText(Paint paint, String text, float maxWidth) {
        if (paint.measureText(text) <= maxWidth) {
            return text;
        }
        String result = text;
        while (paint.measureText(result + "...") > maxWidth && result.length() > 0) {
            result = result.substring(0, result.length() - 1);
        }
        return result + "...";
    }
    
    @Override
    public boolean onTouchEvent(MotionEvent event) {
        // Обработка кликов по кнопкам
        float x = event.getX();
        float y = event.getY();
        
        if (event.getAction() == MotionEvent.ACTION_UP) {
            // TODO: Обработка кликов по кнопкам
        }
        
        return super.onTouchEvent(event);
    }
    
    /**
     * Рисование иконки чата (верхний левый угол, режим без маршрута)
     */
    private void drawChatButton(Canvas canvas, int width, float padding, float topPadding) {
        float buttonSize = 48 * mDp;
        float x = padding;
        float y = topPadding;
        
        mChatButtonRect.set(x, y, x + buttonSize, y + buttonSize);
        
        // Белый круг с тенью
        Paint bgPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
        bgPaint.setColor(Color.WHITE);
        bgPaint.setStyle(Paint.Style.FILL);
        bgPaint.setShadowLayer(4 * mDp, 0, 2 * mDp, 0x40000000);
        canvas.drawCircle(x + buttonSize / 2, y + buttonSize / 2, buttonSize / 2, bgPaint);
        
        // Иконка чата (пузырь с тремя точками)
        Paint iconPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
        iconPaint.setColor(0xFF333333); // Темно-серый
        iconPaint.setStyle(Paint.Style.FILL);
        
        float centerX = x + buttonSize / 2;
        float centerY = y + buttonSize / 2;
        float bubbleSize = buttonSize * 0.5f;
        
        // Пузырь чата
        canvas.drawCircle(centerX, centerY, bubbleSize * 0.6f, iconPaint);
        
        // Три точки
        float dotSize = 3 * mDp;
        float dotSpacing = 6 * mDp;
        canvas.drawCircle(centerX - dotSpacing, centerY, dotSize, iconPaint);
        canvas.drawCircle(centerX, centerY, dotSize, iconPaint);
        canvas.drawCircle(centerX + dotSpacing, centerY, dotSize, iconPaint);
    }
    
    /**
     * Рисование правого сайдбара (режим без маршрута)
     */
    private void drawRightSidebar(Canvas canvas, int width, int height, float padding) {
        float sidebarWidth = 48 * mDp;
        float buttonSize = 48 * mDp;
        float buttonMargin = 8 * mDp;
        float rightX = width - padding - sidebarWidth;
        float currentY = padding;
        
        // Фон сайдбара (белый с тенью)
        Paint sidebarPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
        sidebarPaint.setColor(Color.WHITE);
        sidebarPaint.setStyle(Paint.Style.FILL);
        sidebarPaint.setShadowLayer(4 * mDp, -2 * mDp, 0, 0x40000000);
        
        float sidebarHeight = height - padding * 2;
        canvas.drawRoundRect(new RectF(rightX, padding, width - padding, height - padding),
                            8 * mDp, 8 * mDp, sidebarPaint);
        
        // 1. Меню (три линии) - вверху
        mMenuButtonRect.set(rightX, currentY, rightX + buttonSize, currentY + buttonSize);
        drawMenuIcon(canvas, rightX + buttonSize / 2, currentY + buttonSize / 2, 20 * mDp);
        currentY += buttonSize + buttonMargin;
        
        // 2. Закладка
        mBookmarkButtonRect.set(rightX, currentY, rightX + buttonSize, currentY + buttonSize);
        drawBookmarkIcon(canvas, rightX + buttonSize / 2, currentY + buttonSize / 2, 20 * mDp);
        currentY += buttonSize + buttonMargin;
        
        // 3. Зум + и -
        mZoomInSidebarRect.set(rightX, currentY, rightX + buttonSize, currentY + buttonSize);
        drawZoomIcon(canvas, rightX + buttonSize / 2, currentY + buttonSize / 2, 20 * mDp, true);
        currentY += buttonSize + buttonMargin;
        
        mZoomOutSidebarRect.set(rightX, currentY, rightX + buttonSize, currentY + buttonSize);
        drawZoomIcon(canvas, rightX + buttonSize / 2, currentY + buttonSize / 2, 20 * mDp, false);
        currentY += buttonSize + buttonMargin;
        
        // 4. Центрирование (синяя стрелка вверх)
        mCenterButtonRect.set(rightX, currentY, rightX + buttonSize, currentY + buttonSize);
        drawCenterIcon(canvas, rightX + buttonSize / 2, currentY + buttonSize / 2, 24 * mDp);
        currentY += buttonSize + buttonMargin;
        
        // 5. Поиск (лупа) - внизу
        mSearchSidebarRect.set(rightX, height - padding - buttonSize, rightX + buttonSize, height - padding);
        drawSearchIcon(canvas, rightX + buttonSize / 2, height - padding - buttonSize / 2, 20 * mDp);
    }
    
    /**
     * Рисование нижней панели с избранными местами
     */
    private void drawFavoritePlacesBar(Canvas canvas, int width, int height, float padding) {
        float barHeight = 60 * mDp;
        float barY = height - padding - barHeight;
        
        // Фон панели (белый с тенью)
        Paint barPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
        barPaint.setColor(Color.WHITE);
        barPaint.setStyle(Paint.Style.FILL);
        barPaint.setShadowLayer(4 * mDp, 0, -2 * mDp, 0x40000000);
        canvas.drawRoundRect(new RectF(padding, barY, width - padding, height - padding),
                            8 * mDp, 8 * mDp, barPaint);
        
        // Текст избранных мест
        mTextPaint.setTextSize(16 * mDp);
        mTextPaint.setColor(0xFF333333);
        mTextPaint.setTypeface(Typeface.create(Typeface.DEFAULT, Typeface.NORMAL));
        
        float textX = padding + 16 * mDp;
        float textY = barY + barHeight / 2 + 8 * mDp;
        float itemSpacing = 24 * mDp;
        
        for (int i = 0; i < mFavoritePlaces.length && i < 2; i++) {
            String place = mFavoritePlaces[i];
            int time = mFavoriteTimes[i];
            String text = place + " " + time + " мин.";
            
            canvas.drawText(text, textX, textY, mTextPaint);
            textX += mTextPaint.measureText(text) + itemSpacing;
        }
    }
    
    /**
     * Рисование иконки меню (три линии)
     */
    private void drawMenuIcon(Canvas canvas, float centerX, float centerY, float size) {
        Paint iconPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
        iconPaint.setColor(0xFF333333);
        iconPaint.setStyle(Paint.Style.STROKE);
        iconPaint.setStrokeWidth(2.5f * mDp);
        iconPaint.setStrokeCap(Paint.Cap.ROUND);
        
        float lineLength = size * 0.6f;
        float lineSpacing = size * 0.2f;
        
        // Три горизонтальные линии
        for (int i = 0; i < 3; i++) {
            float y = centerY - lineSpacing + i * lineSpacing;
            canvas.drawLine(centerX - lineLength / 2, y, centerX + lineLength / 2, y, iconPaint);
        }
    }
    
    /**
     * Рисование иконки закладки
     */
    private void drawBookmarkIcon(Canvas canvas, float centerX, float centerY, float size) {
        Paint iconPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
        iconPaint.setColor(0xFF333333);
        iconPaint.setStyle(Paint.Style.STROKE);
        iconPaint.setStrokeWidth(2.5f * mDp);
        iconPaint.setStrokeCap(Paint.Cap.ROUND);
        iconPaint.setStrokeJoin(Paint.Join.ROUND);
        
        Path path = new Path();
        float halfSize = size * 0.4f;
        
        // Закладка (сложенный лист)
        path.moveTo(centerX, centerY - halfSize);
        path.lineTo(centerX + halfSize * 0.6f, centerY);
        path.lineTo(centerX, centerY + halfSize * 0.8f);
        path.lineTo(centerX - halfSize * 0.6f, centerY);
        path.close();
        
        canvas.drawPath(path, iconPaint);
    }
    
    /**
     * Рисование иконки центрирования (синяя стрелка вверх)
     */
    private void drawCenterIcon(Canvas canvas, float centerX, float centerY, float size) {
        // Фон (белый круг)
        Paint bgPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
        bgPaint.setColor(Color.WHITE);
        bgPaint.setStyle(Paint.Style.FILL);
        canvas.drawCircle(centerX, centerY, size / 2, bgPaint);
        
        // Синяя стрелка вверх
        Paint arrowPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
        arrowPaint.setColor(0xFF1E88E5); // Синий Яндекс
        arrowPaint.setStyle(Paint.Style.FILL);
        
        Path path = new Path();
        float halfSize = size * 0.4f;
        
        path.moveTo(centerX, centerY - halfSize);
        path.lineTo(centerX - halfSize * 0.6f, centerY);
        path.lineTo(centerX + halfSize * 0.6f, centerY);
        path.close();
        
        canvas.drawPath(path, arrowPaint);
    }
}
