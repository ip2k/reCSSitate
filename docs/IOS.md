# Install reCSSitate in Safari on iPhone

After installing the [Userscripts app](https://github.com/quoid/userscripts),
enable its Safari extension and allow access to your reader server and the sites
where you want the rescue button. Open your reader's landing page in Safari and
tap **Install reCSSitate userscript**. Seeing JavaScript source is expected.

## 1. Open Userscripts

Open Safari's page/extension menu and choose **Userscripts**.

<img src="../web/assets/ios-install/01-open-userscripts.png" alt="Arrow pointing to the Userscripts entry in Safari's extension menu." width="640">

## 2. Tap the yellow install banner

In the Userscripts popup, tap **Userscript Detected: Tap to install**.

<img src="../web/assets/ios-install/02-detected.png" alt="Arrow pointing to the yellow Tap to install banner in the Userscripts popup." width="640">

## 3. Confirm Install

Check that the script is **reCSSitate**, review its details, and tap the blue
**Install** button at the bottom. The checkmark at the top closes the popup;
it is not the Install button.

<img src="../web/assets/ios-install/03-install.png" alt="Arrow pointing to the blue Install button at the bottom of the confirmation screen." width="640">

## 4. Check the green confirmation

The banner changes to **Userscript Installed: Tap to re-install**. Installation
is complete; you do not need to tap the banner again. Leave the extension's switch
on and tap the blue checkmark to close the popup.

<img src="../web/assets/ios-install/04-installed.png" alt="Green installed confirmation banner, with an arrow pointing to the blue Done checkmark." width="640">

Return to an article and reload it if it was already open. reCSSitate offers
**Read article** when it detects a persistent large anti-adblock obstruction.
A readable page will not show the button. If Safari asks for website access,
grant access on the sites where you want the script to run.

If no yellow banner appears, make sure Safari is showing the `.user.js` link
from your own reader server and Userscripts has access to that server.

These annotated illustrations are adapted from user-supplied screenshots.
Code and deployment details have been omitted. Layout may vary by iOS and
Userscripts version.
