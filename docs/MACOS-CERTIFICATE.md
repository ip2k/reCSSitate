# Trust your reader's certificate on macOS

For a reader using Caddy's local CA, import its **public root certificate**, then
enable trust in Keychain Access. Skip this guide if your reader already uses a
publicly trusted certificate. Importing alone does not enable trust.

## 1. Download your reader's certificate

Open `http://YOUR-HOST:8086/` on your reader's network and click **Download this
reader’s CA certificate**. The direct download is
`http://YOUR-HOST:8086/reader-ca.crt`. Replace `YOUR-HOST` and the setup port with
your deployment's values. Save the file as `reader-ca.crt` in Downloads.

The reader's landing page also links to this download and the setup page. The
links there already use your server's address; GitHub cannot determine it.

Confirm the certificate name and SHA-256 fingerprint with your administrator
through a trusted channel. You can inspect the downloaded public certificate:

```sh
openssl x509 -in "$HOME/Downloads/reader-ca.crt" -noout -subject -fingerprint -sha256
```

A trusted root can validate certificates for other sites too. Install only your
administrator's certificate, never a CA private key or a tutorial's demo root.

## 2. Import it into Keychain Access

1. Open **Keychain Access** using Spotlight (**Command–Space**). If macOS offers
   the Passwords app, choose **Open Keychain Access**.
2. Select **System** in the keychain sidebar. This makes the root available to
   users of this Mac and may require an administrator password.
3. Choose **File → Import Items…**, select `reader-ca.crt`, and click **Open**.
   Dragging the file into the selected keychain also works.
4. Select the **Certificates** category and find the imported root. Caddy's
   default name usually starts with **Caddy Local Authority**; your administrator
   may have chosen another name. Do not select an unrelated certificate.

See [Apple's certificate import instructions](https://support.apple.com/guide/keychain-access/kyca2431/mac).

## 3. Enable trust

1. Double-click the imported root certificate and expand **Trust**.
2. Set **When using this certificate** to **Always Trust**.
3. Close the certificate window to save. Authenticate with your **Mac
   administrator credentials** if asked; these are separate from reader login.

See [Apple's certificate trust instructions](https://support.apple.com/guide/keychain-access/kyca11871/mac).

## 4. Verify in Safari

Open `https://YOUR-HOST:8446/`. It should load without a certificate warning.
If an existing Safari tab keeps the old error, close that tab and reopen the URL;
quit and reopen Safari if necessary. Reader authentication is off by default.

If a warning remains, check that you trusted the correct root, that the hostname
or IP matches the server certificate, and that the Mac's date and time are
correct. An expired certificate or name mismatch needs a server fix. Other
applications can use their own certificate stores; this guide targets Safari
and applications using macOS trust.

## Remove or replace the root

In Keychain Access, select **System → Certificates**, identify this exact root,
and delete it, authenticating if prompted. Remove only the root you installed.
If your administrator replaces the CA, install and trust the new root, then
remove the retired one when it is no longer needed by your services.

For the server-side download and fingerprint commands, see the
[administrator section of the certificate guide](IOS-CERTIFICATE.md#for-the-server-administrator).
