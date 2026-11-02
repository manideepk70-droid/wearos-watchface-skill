# Watch Face Format (WFF) v1 cheat sheet

A WFF face is an APK with no code: `AndroidManifest.xml` (with the
`com.google.wear.watchface.format.version` property and `hasCode="false"`),
`res/xml/watch_face_info.xml`, `res/raw/watchface.xml` and images in
`res/drawable-nodpi/`. Needs Wear OS 4 (API 33) or newer.

## Coordinates

- `<WatchFace width="450" height="450">` defines a design grid; the watch scales it to
  its screen. Make images at the watch's real pixel size (or a little above for
  sharpness), not larger.
- Use **whole numbers** for `x`, `y`, `width`, `height` (decimals can fail to load).
- Angles: 0 = 12 o'clock, clockwise.

## Building blocks

```xml
<Scene backgroundColor="#FF000000"> ... </Scene>            <!-- colours are #AARRGGBB -->
<Group name="g" x="0" y="0" width="450" height="450"> ... </Group>
<PartImage x="0" y="0" width="450" height="450"><Image resource="bg"/></PartImage>
<PartText x="75" y="100" width="300" height="30">
  <Text align="CENTER">                                       <!-- START, CENTER, END -->
    <Font family="SYNC_TO_DEVICE" size="22" weight="SEMI_BOLD" color="#FFFFFFFF">
      <Template>%s %s<Parameter expression="[MONTH_S]"/><Parameter expression="[DAY]"/></Template>
    </Font>
  </Text>
</PartText>
<DigitalClock x="0" y="140" width="450" height="120">
  <TimeText format="hh:mm" align="CENTER" x="0" y="0" width="450" height="120">  <!-- HH:mm = 24 h -->
    <Font family="SYNC_TO_DEVICE" size="104" weight="LIGHT" color="#FFFFFFFF"/>
  </TimeText>
</DigitalClock>
<PartDraw x="0" y="0" width="450" height="450">
  <Arc centerX="225" centerY="225" width="420" height="420" startAngle="0" endAngle="0">
    <Transform target="endAngle" value="clamp([BATTERY_PERCENT], 0, 100) * 3.6"/>
    <Stroke color="#FFFFC14D" thickness="5" cap="ROUND"/>
  </Arc>
</PartDraw>
```

Put a literal `%` in its own `PartText` next to the number instead of inside the template.

## Data (built in, every watch)

| Expression | Value |
|---|---|
| `[STEP_COUNT]`, `[STEP_PERCENT]` | steps today, % of step goal |
| `[BATTERY_PERCENT]` | battery 0-100 |
| `[DAY]`, `[MONTH_S]`, `[DAY_OF_WEEK_S]` | 29, Oct, Wed |
| `[SECONDS_IN_DAY]`, `[SECOND]` | avoid: forces a redraw every second |
| `numberFormat("#,##0", [STEP_COUNT])` | 8,532 |

## Always-on (ambient) mode

```xml
<Variant mode="AMBIENT" target="alpha" value="0"/>     <!-- first child: hide in always-on -->
<Variant mode="AMBIENT" target="alpha" value="170"/>   <!-- dim -->
```

## Conditions

```xml
<Condition>
  <Expressions><Expression name="low">[BATTERY_PERCENT] &lt;= 20</Expression></Expressions>
  <Compare expression="low"> ... shown when true ... </Compare>
  <Default> ... otherwise ... </Default>
</Condition>
```
Escape `<`, `>` and `&` in expressions (`&lt;`, `&gt;`, `&amp;`).

## Bitmap fonts (custom lettering)

```xml
<WatchFace ...>
  <BitmapFonts>
    <BitmapFont name="tw">
      <Character name="0" resource="tw_0" width="48" height="62"/>  <!-- design units -->
      ...
    </BitmapFont>
  </BitmapFonts>
  <Scene> ... <TimeText ...><BitmapFont family="tw" size="62"/></TimeText> ... </Scene>
</WatchFace>
```
`scripts/fontkit.py` writes the images and this XML.

## Animation (use sparingly)

```xml
<PartAnimatedImage x="..." y="..." width="..." height="...">
  <AnimationController play="ON_VISIBLE TAP" loopCount="1" beforePlaying="FIRST_FRAME" afterPlaying="FIRST_FRAME"/>
  <AnimatedImage resource="anim" format="WEBP"/>
</PartAnimatedImage>
```
Animate only the part that moves, play once, never loop forever.

## Install and switch

```
adb install -r build/face.apk
adb shell am broadcast -a com.google.android.wearable.app.DEBUG_SURFACE \
  --es operation set-watchface --es watchFaceId <package>
```

## Validate

The official XSD schemas live in the `google/watchface` repository on GitHub. Some
`xmllint` versions reject them as-is; a local copy where `xs:all` is changed to
`xs:choice` (and a self-include removed) validates fine. If a face shows a blank screen,
check `adb logcat | grep -i watchface` for the parse error.
