# MyFlightbook

This repository contains both the legacy MyFlightbook application and the side-by-side migration workspace that is replacing it.

## Start Here

Use the path that matches the kind of work you are doing.

### Discussing New Features Or Contract Changes

1. [Change Intake Protocol](docs/changes/change-intake-protocol.md) for the official discussion and approval workflow.
2. [Approved Change Register](docs/changes/approved-change-register.md) for explicitly approved changes waiting for or already past rowization.
3. [Feature Discussion Start Prompt](docs/agents/feature-discussion-start-prompt.md) to bootstrap a fresh discussion agent.

Discussion ends in a proposal state. Execution does not start until an explicitly approved change is rowized into exact ledger rows.

### Executing Approved Work

1. [Repo Completion Protocol](docs/migration/repo-completion-protocol.md) for the repo-wide execution loop and strict finish line.
2. [Parity Status Ledger](docs/migration/parity-status-ledger.md) for the live execution state and next incomplete slice.
3. [Legacy Contract Inventory](docs/migration/contract-inventory.md) for the canonical family order and census source.
4. [Migration Execution Playbook](docs/migration/execution-playbook.md) for the exact workflow to migrate one ledger row.
5. [Local Development Infrastructure](docs/infrastructure/local-dev.md) for environment truth and startup modes.
6. [Migration Bootstrap Guide](docs/migration/bootstrap.md) for the current stack, what is already implemented, and what remains deferred.

## Repository Lanes

### Migration Workspace (default)

The new stack lives beside the legacy code and should be the default place to work unless a task explicitly targets the reference system.

- `apps/api`: FastAPI + SQLAlchemy + Alembic backend
- `apps/web`: Next.js App Router frontend
- `apps/worker`: `arq` worker for telemetry and media jobs
- `packages/api-client`: shared TypeScript API client generated from FastAPI OpenAPI
- `docs/changes`: feature and contract-change intake docs
- `docs/migration`: parity scope, repo-completion loop, execution workflow, and migration notes
- `infra/docker-compose.yml`: Postgres, Redis, MinIO, and worker for the full parity environment
- `agents.md`: AI-agent entrypoint for this workspace

### Legacy Reference Environment

The legacy system remains the reference behavior and import source.

- `MyFlightbook.Web`: ASP.NET application, SOAP/mobile API host, MVC controllers, and embedded domain behavior
- `MyFlightbook.*`: supporting .NET libraries and shared utilities
- `MyFlightbook.Web/Support/MinimalDB-2026-01-29.sql`: baseline schema reference for legacy data import and parity work

## Migration Dev Modes

Use one of these modes intentionally. They are not the same environment.

| Mode | Command | Starts | Does not start | Best for |
| --- | --- | --- | --- | --- |
| Windows fast path | `powershell -ExecutionPolicy Bypass -File .\scripts\dev-up.ps1 -Seed` | Alembic migration, local PostgreSQL service if present, MinIO, API, web, demo seed | Redis, worker, Docker services | Daily API and web iteration |
| Full container/parity path | `docker compose -f .\infra\docker-compose.yml up -d postgres redis minio worker` | Postgres, Redis, MinIO, worker | API, web, demo seed | Worker work, Redis-backed flows, parity verification |

Important notes:

- `powershell -ExecutionPolicy Bypass -File .\scripts\dev-down.ps1` stops only the API, web, and MinIO processes started from this repo. It does not stop Docker services or the PostgreSQL Windows service.
- The Docker compose file does not start the FastAPI or Next.js dev servers. Start those separately when using the full parity path.

## Change And Execution Workflow

For feature discussions and contract changes:

1. Produce a decision-complete proposal under `docs/changes/proposals/<change-id>/proposal.md`.
2. Keep the proposal at `proposed` until you explicitly approve it.
3. Only after approval may the proposal, approved change register, and contract inventory be updated.
4. Let the Architect rowize the approved change into exact execution rows.
5. Execution begins only after the change reaches `rowized`.

For each approved parity or feature row:

1. Check the approved change register first. If an approved change is still unrowized, the Architect owns the next step.
2. Otherwise find the next incomplete row in [parity-status-ledger.md](docs/migration/parity-status-ledger.md).
3. Use [repo-completion-protocol.md](docs/migration/repo-completion-protocol.md) to decide whether the next owner is Architect, Feature Scaffolder, or Coder.
4. Follow [execution-playbook.md](docs/migration/execution-playbook.md) to capture fixtures, map contracts, and define the acceptance checks for that row.
5. Implement the backend compatibility behavior first, then update the typed client, then add or adjust web UI only if the row needs it.
6. Add worker work only when the row truly requires async processing.
7. Verify the row with parity-oriented tests before advancing the ledger.

## Legacy Reference Environment Setup

This section is for standing up the legacy system as a reference environment. It is not the default path for migration work.

### Setting Up The Website

- Run on any Windows machine with ASP.NET 4.5 or later.
- Make sure IIS has ASP turned on under "application development features".
- Make sure IIS has HTTP Redirection turned on under Internet Information Services/World Wide Web Services/Common HTTP Features.
- Create 6 folders under `Images`: `Aircraft`, `BasicMed`, `Endorsements`, `OfflineEndorsements`, `Flights`, and `Telemetry`. Set permissions so that Network Service has full control.
- Add the following `web.config` to the `Telemetry` folder so that telemetry cannot be served directly:

```xml
<?xml version="1.0"?>
<configuration>
  <system.webServer>
    <authorization>
      <deny users="?" />
      <deny users="*"/>
    </authorization>
  </system.webServer>
</configuration>
```

- Set up the virtual directory for `logbook` pointing to your working directory and convert it to an application. Use ASP.NET 4.5 or later as the application pool.
- Set up a certificate to enable HTTPS.
- Make sure IIS is configured to serve `.KML`, `.GPX`, `.PDF`, `.JPG`, `.DOCX`, `.APK`, and similar file types.
- Add `email.config` to `App_Data`:

```xml
<?xml version="1.0"?>
<smtp deliveryMethod="Network" from="(your email address)">
    <network defaultCredentials="false" port="587" host="..." userName="..." password="..." />
</smtp>
```

- Add `connection.config` to `App_Data`:

```xml
<?xml version="1.0"?>
<connectionStrings>
  <add name="logbookConnectionString" connectionString="server=...;User Id=...;password=...;Persist Security Info=false;database=logbook;CharSet=utf8mb4;Pooling=false" providerName="MySql.Data.MySqlClient" />
</connectionStrings>
```

- Review `Packages.config` and install the required products and DLLs into the `Bin` directory.

### Setting Up The Database

- Install MySQL and import `MinimalDB-xxxx-xx-xx.sql` from the `Support` folder, then apply any newer scripts in that folder.
- Populate the `LocalConfig` table with the values needed for integrations, mapping, media, and authentication.
- Increase packet size to at least 10-15 MB: `show variables like 'max_allowed_packet';` then `SET GLOBAL max_allowed_packet=16777216`.
- Consider increasing `group_concat_max_len` to at least `2048`.
- Depending on hosting, you may need `lower_case_table_names=1`.
- MySQL 5.7 environments may require `sql_mode=ALLOW_INVALID_DATES`.

#### LocalConfig Settings

- `AdminAuthAccessKey`: Enables certain admin-only functionality and provides an encryption seed.
- `AuthorizedWebServiceClients`: Comma-separated list of authorized mobile and web-service clients.
- `AWSAccessKey`: Access key for Amazon Web Services.
- `AWSMediaConvertRoleArn`: ARN for converting media files on AWS.
- `AWSSecretKey`: Secret for Amazon Web Services.
- `BoxClientID`: OAuth client ID for Box.com.
- `BoxClientSecret`: OAuth secret for Box.com.
- `CloudAhoyID`: OAuth client ID for CloudAhoy.
- `CloudAhoySecret`: OAuth secret for CloudAhoy.
- `DebugDomains`: Local domains from which OAuth requests may originate.
- `DropboxAccessID`: Access key for Dropbox.
- `DropboxClientSecret`: Secret for Dropbox.
- `ETSPipelineID`: Amazon Elastic Transcoder pipeline ID for production video processing.
- `ETSPipelineIDDebug`: Elastic Transcoder pipeline ID for development.
- `ETSPipelineIDStaging`: Elastic Transcoder pipeline ID for staging.
- `FacebookAccessID`: Facebook access key. Obsolete.
- `facebookAppId`: Facebook page application ID.
- `FacebookClientSecret`: Facebook secret. Obsolete.
- `FlightCrewViewClientID`: OAuth client ID for FlightCrewView.
- `FlightCrewViewClientSecret`: OAuth secret for FlightCrewView.
- `FlyStoAccessID`: OAuth client ID for FlySto.
- `FlyStoClientSecret`: OAuth secret for FlySto.
- `GoogleAdClient`: Google AdSense client ID.
- `GoogleAdHorizontalSlot`: Horizontal AdSense slot ID.
- `GoogleAdVerticalSlot`: Vertical AdSense slot ID.
- `GoogleAnalyticsDeveloper`: Developer Google Analytics ID. Obsolete.
- `GoogleAnalyticsProduction`: Production Google Analytics ID. Obsolete.
- `GoogleAnalyticsGA4Developer`: Developer Google Analytics GA4 ID.
- `GoogleAnalyticsGA4Production`: Production Google Analytics GA4 ID.
- `GoogleDriveAccessID`: OAuth client ID for Google Drive.
- `GoogleDriveClientSecret`: OAuth secret for Google Drive.
- `GoogleMapID`: Google Maps ID used for AdvancedMarkerElement and reCAPTCHA.
- `GoogleMapsKey`: Google Maps API key.
- `GooglePlusAccessID`: Google Plus access key. Obsolete.
- `GooglePlusAPIKey`: Google Plus API key. Obsolete.
- `GooglePlusClientSecret`: Google Plus secret. Obsolete.
- `GroundSchoolDiscountLink`: Promotion markup for a donation tier.
- `LeonClientID`: OAuth client ID for Leon Scheduling.
- `LeonClientSecret`: OAuth secret for Leon Scheduling.
- `OneDriveAccessID`: OAuth client ID for OneDrive.
- `OneDriveClientSecret`: OAuth secret for OneDrive.
- `PeerRequestEncryptorKey`: Key for peer-to-peer request encryption.
- `rbClientID`: Production OAuth client ID for RosterBuster.
- `rbClientDIDDev`: Development OAuth client ID for RosterBuster.
- `recaptchaKey`: Google reCAPTCHA key.
- `recaptchValidateEndpoint`: URL for reCAPTCHA validation.
- `SharedDataEncryptorKey`: Key used to encrypt shared public data.
- `ShuntState`: Use `shunted` to shunt the site.
- `ShuntMessage`: Message shown while the site is shunted.
- `StripeLiveKey`: Live Stripe key.
- `StripeLiveWebhook`: Live Stripe webhook.
- `StripeTestKey`: Test Stripe key.
- `StripeTestWebhook`: Test Stripe webhook.
- `TwitterAccessID`: Twitter access ID. Obsolete.
- `TwitterClientSecret`: Twitter secret. Obsolete.
- `UseAWSS3`: Set to `yes` to migrate images to S3. Leave `no` for local debugging.
- `UseOOF`: Set to `yes` to auto-respond to contact-me requests with an out-of-office message.
- `UserAccessEncryptorKey`: Key used to share flights.
- `UserPasswordHashKey`: Hash key used when storing user password hashes.
- `WebAccessEncryptorKey`: Key used to encrypt and decrypt web-service authorizations.
- `wkhtmlpath`: Full filesystem path to `wkhtmltopdf.exe`.

The following keys define application-relative media directories:

- `AircraftPixDir`
- `FlightsPixDir`
- `BasicMedDir`
- `TelemetryDir`
- `EndorsementsPixDir`
- `OfflineEndorsementsPixDir`

### Additional Items

- Install [WKHtmlToPdf](http://wkhtmltopdf.org/) to generate PDFs.

### Live Site Only

The following tasks are for the live legacy site only:

- Set up a scheduled task to send nightly stats, delete Dropbox cache, and send nightly email.
- Install root files from the `Support` directory so that `http://.../` resolves to the default home page and `favicon.ico` works.
- Ensure reverse DNS is configured so that email can be received.
- Configure custom errors in `web.config`, but turn them off in IIS so that OAuth errors are still visible during debugging.
- Use a custom application pool and configure daily recycling and memory recycling.
- Ensure port `3306` is closed and the firewall is appropriately configured.

## Additional Attributions And Licenses

This source code is provided under the GNU license, but it incorporates other code as well from a variety of other sources, and each such work is covered by its respective license. This includes, but is not limited to:

- [Ourairports](https://github.com/davidmegginson/ourairports-data) - Open database of worldwide airports.
- [DayPilot](https://javascript.daypilot.org/) - Calendar code for club aircraft scheduling.
- [CSV utilities](http://www.heikniemi.fi/jhlib/) - Read and write CSV data.
- [EXIF utilities](https://www.codeproject.com/Articles/7888/A-library-to-simplify-access-to-image-metadata) - Read and write image metadata.
- OAuth1 support for Twitter with source included in the repo.
- [DotNetOpenAuth](http://dotnetopenauth.net/) - OAuth2 client and server support.
- NOAA celestial code for day and night calculations.
- [Membership and Role management](https://www.codeproject.com/Articles/12301/Membership-and-Role-providers-for-MySQL) for MySQL-backed auth.
- [wkHtmlTox](https://wkhtmltopdf.org/) for HTML-to-PDF rendering.
- [SecuritySwitch](https://www.nuget.org/packages/SecuritySwitch/4.4.0) for HTTP and HTTPS declaration.
- [Endless Scroll](https://github.com/fredwu/jquery-endless-scroll) for endless scrolling.
- [JQuery](http://jquery.org) and additional JavaScript libraries.
- [OverlappingMarkerSpiderfier](https://github.com/jawj/OverlappingMarkerSpiderfier) for map marker handling.
- [Scribble-signature control](https://www.codeproject.com/Articles/432675/Building-a-Signature-Control-Using-Canvas) for signature capture.
- [Todataurl-png.js](http://code.google.com/p/todataurl-png-js/) for bitmap-to-data-URL conversion.
- [DotNetZip](https://dotnetzip.codeplex.com/) for zip support.
- [BxSlider](http://bxslider.com/) for image slideshows.
- [ImageMagick](https://github.com/dlemstra/Magick.NET) for HEIC support.
