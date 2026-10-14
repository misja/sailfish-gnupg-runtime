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
    if (args.size() == 2 && args[1] == "state") {
        report(QJsonObject{{"device_lock_state", lockState()}}); return 0;
    }
    if (args.size() != 4) return 64;
    if (args[1] != "request") return 64;
    const QString action = QString::fromLatin1(qgetenv("SYNTHETIC_POLICY_ACTION"));
    const QString token = args[2], policy = args[3];
    if (!QRegExp("[0-9a-f]{24}").exactMatch(token)) return 64;
    if (policy != "keep" && policy != "verify" && policy != "relock") return 64;
    if (action != "create" && action != "store" && action != "get" &&
        action != "get-ui" && action != "delete") return 64;
    const QString collection = "SPP" + token + (policy == "keep" ? "K" : policy == "verify" ? "V" : "R");
    const QString plugin = S::SecretManager::DefaultEncryptedStoragePluginName;
    const S::Secret::Identifier identifier("synthetic-passphrase", collection, plugin);
    const QByteArray expected("test-123"); // Public synthetic vector only.
    const int before = lockState();
    if ((action == "create" || action == "store") && before != 0) {
        report(QJsonObject{{"action", action}, {"collection", collection}, {"policy", policy},
                          {"device_lock_state_before", before}, {"refused_not_unlocked", true}});
        return 65;
    }
    S::SecretManager manager;
    S::CreateCollectionRequest create;
    S::StoreSecretRequest store;
    S::StoredSecretRequest get;
    S::DeleteCollectionRequest remove;
    S::Request *request = nullptr;
    if (action == "create") {
        create.setCollectionName(collection);
        create.setStoragePluginName(plugin);
        create.setEncryptionPluginName(plugin);
        create.setCollectionLockType(S::CreateCollectionRequest::DeviceLock);
        create.setDeviceLockUnlockSemantic(policy == "keep" ? S::SecretManager::DeviceLockKeepUnlocked :
            policy == "verify" ? S::SecretManager::DeviceLockVerifyLock : S::SecretManager::DeviceLockRelock);
        create.setAccessControlMode(S::SecretManager::OwnerOnlyMode);
        create.setUserInteractionMode(S::SecretManager::SystemInteraction);
        request = &create;
    } else if (action == "store") {
        S::Secret secret(identifier);
        secret.setType(S::Secret::TypeBlob);
        secret.setData(expected);
        store.setSecret(secret);
        store.setSecretStorageType(S::StoreSecretRequest::CollectionSecret);
        store.setUserInteractionMode(S::SecretManager::SystemInteraction);
        request = &store;
    } else if (action == "get" || action == "get-ui") {
        get.setIdentifier(identifier);
        get.setUserInteractionMode(action == "get" ? S::SecretManager::PreventInteraction : S::SecretManager::SystemInteraction);
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
