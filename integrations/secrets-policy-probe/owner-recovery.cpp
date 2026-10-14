// Synthetic policy investigation, 2026-10-12. Not a production cache helper.
#include <QCoreApplication>
#include <QEventLoop>
#include <QTimer>
#include <QJsonDocument>
#include <QJsonObject>
#include <QRegExp>
#include <QDBusConnection>
#include <QDBusMessage>
#include <QDBusVariant>
#include <Secrets/secretmanager.h>
#include <Secrets/createcollectionrequest.h>
#include <Secrets/storesecretrequest.h>
#include <Secrets/storedsecretrequest.h>
#include <Secrets/deletecollectionrequest.h>
#include <sys/resource.h>
#include <unistd.h>
#include <cstdio>
namespace S = Sailfish::Secrets;

static int lockState()
{
    QDBusMessage message = QDBusMessage::createMethodCall(
        "org.nemomobile.devicelock", "/devicelock",
        "org.freedesktop.DBus.Properties", "Get");
    message << QString("org.nemomobile.devicelock.DeviceLock") << QString("State");
    QDBusMessage reply = QDBusConnection::systemBus().call(message, QDBus::Block, 5000);
    if (reply.type() != QDBusMessage::ReplyMessage || reply.arguments().size() != 1)
        return -1;
    bool valid = false;
    uint state = qvariant_cast<QDBusVariant>(reply.arguments().at(0)).variant().toUInt(&valid);
    return valid && state <= 4 ? int(state) : -1;
}

static void report(QJsonObject result)
{
    QByteArray line = QJsonDocument(result).toJson(QJsonDocument::Compact);
    fwrite(line.constData(), 1, size_t(line.size()), stdout);
    fputc('\n', stdout); fflush(stdout);
}

static bool perform(S::Request &request)
{
    QEventLoop loop;
    QTimer timeout;
    timeout.setSingleShot(true);
    bool expired = false;
    QObject::connect(&timeout, &QTimer::timeout, [&] { expired = true; loop.quit(); });
    QObject::connect(&request, &S::Request::statusChanged, [&] {
        if (request.status() == S::Request::Finished) loop.quit();
    });
    timeout.start(60000);
    request.startRequest();
    if (request.status() != S::Request::Finished) loop.exec();
    return !expired && request.status() == S::Request::Finished;
}

int main(int argc, char **argv)
{
    if (getuid() != 100000) return 64;
    struct rlimit limit = {0, 0};
    if (setrlimit(RLIMIT_CORE, &limit)) return 64;
    alarm(75); // Last-resort bound; does not promise system-dialog dismissal.
    QCoreApplication app(argc, argv);
    app.setApplicationName("sailfish-synthetic-secrets-policy-probe");
    const QStringList args = app.arguments();
    // Preserve the recorded creating command line; allow only bounded cleanup.
    if (args.size() != 4 || args[0] != "/var/tmp/sailfish-secrets-policy-5JamYk/secrets-policy-probe"
            || args[1] != "create" || args[2] != "4245823b8da845a29bef5e45" || args[3] != "keep") return 64;
    const QByteArray mode = qgetenv("SYNTHETIC_OWNER_RECOVERY");
    if (mode != "get" && mode != "delete") return 64;
    const QString action = QString::fromLatin1(mode);
    const QString policy = "keep";
    const QString collection = "SPP4245823b8da845a29bef5e45K";
    const QString plugin = S::SecretManager::DefaultEncryptedStoragePluginName;
    const S::Secret::Identifier identifier("synthetic-passphrase", collection, plugin);
    const QByteArray expected("test-123"); // Public synthetic vector only.
    const int before = lockState();
    if (before != 0) {
        report(QJsonObject{{"action", action}, {"collection", collection}, {"policy", policy},
                          {"device_lock_state_before", before}, {"refused_not_unlocked", true}});
        return 65;
    }
    S::SecretManager manager;
    S::StoredSecretRequest get;
    S::DeleteCollectionRequest remove;
    S::Request *request = nullptr;
    if (action == "get") {
        get.setIdentifier(identifier);
        get.setUserInteractionMode(S::SecretManager::PreventInteraction);
        request = &get;
    } else {
        remove.setCollectionName(collection);
        remove.setStoragePluginName(plugin);
        remove.setUserInteractionMode(S::SecretManager::SystemInteraction);
        request = &remove;
    }
    request->setManager(&manager);
    const bool finished = perform(*request);
    const S::Result result = request->result();
    QJsonObject record{{"action", action}, {"collection", collection}, {"policy", policy},
        {"finished", finished}, {"result", int(result.code())}, {"error", int(result.errorCode())},
        {"device_lock_state_before", before}, {"device_lock_state_after", lockState()}};
    bool matches = true;
    if ((action == "get" || action == "get-ui") && result.code() == S::Result::Succeeded) {
        matches = get.secret().data() == expected;
        record.insert("synthetic_bytes_match", matches);
    }
    report(record);
    return !finished ? 124 : result.code() != S::Result::Succeeded ? 2 : !matches ? 3 : 0;
}
