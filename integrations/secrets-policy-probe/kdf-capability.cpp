// Read-only provider capability diagnosis. Public synthetic vectors only.
// Wire schema pinned to Sailfish Secrets 0.2.44 serialization.cpp.
#include <QCoreApplication>
#include <QDBusArgument>
#include <QDBusConnection>
#include <QDBusMessage>
#include <QDBusMetaType>
#include <QJsonDocument>
#include <QJsonObject>
#include <QVariantMap>
#include <sys/resource.h>
#include <unistd.h>
#include <cstdio>
static void enumInt(QDBusArgument &a,int v) { a.beginStructure();a<<v;a.endStructure(); }
static QDBusArgument keyTemplate() {
 QDBusArgument a;a.beginStructure();a.beginStructure();
 a<<QString()<<QString()<<QString();a.endStructure();
 a<<int(0)<<int(260)<<int(0)<<int(7)<<int(256);
 a<<QByteArray()<<QByteArray()<<QByteArray()<<QList<QByteArray>();
 a.beginStructure();a<<QVariantMap();a.endStructure();a.endStructure();return a;
}
static QDBusArgument pairParams() {
 QDBusArgument a;a.beginStructure();a<<int(0)<<QVariantMap()<<QVariantMap();a.endStructure();return a;
}
static QDBusArgument kdfParams(int iterations) {
 QDBusArgument a;a.beginStructure();a<<QByteArray("test-123")<<QByteArray("SyntheticPublicSalt");
 enumInt(a,10);enumInt(a,10);enumInt(a,0);enumInt(a,23);
 a<<qint64(0)<<iterations<<int(0)<<int(256)<<QVariantMap();a.endStructure();return a;
}
static void output(const QJsonObject &o) {
 QByteArray b=QJsonDocument(o).toJson(QJsonDocument::Compact);fwrite(b.constData(),1,b.size(),stdout);fputc('\n',stdout);fflush(stdout);
}
int main(int argc,char **argv) {
 if(getuid()!=100000 || argc!=1)return 64;
 rlimit limit={0,0};if(setrlimit(RLIMIT_CORE,&limit))return 64;alarm(45);
 QCoreApplication app(argc,argv);qDBusRegisterMetaType<QList<QByteArray>>();
 QDBusConnection connection=QDBusConnection::connectToPeer("unix:path=/run/user/100000/sailfishsecretsd/p2pSocket","synthetic-kdf-capability");
 if(!connection.isConnected()){output({{"connection_failed",true}});return 1;}
 const int rounds[]={12000,16000};
 const char *expected[]={"e96d100810c548dd23d3fc87cfbd26cbcdeea9ce9cb6e14730909c44adee52de","0f839f40015f66eda8991bfd171ae3ba767e947138317a49bb570e64906552a2"};
 for(int index=0;index<2;++index) {
  QDBusMessage m=QDBusMessage::createMethodCall("org.sailfishos.crypto.daemon","/Sailfish/Crypto","org.sailfishos.crypto","generateKey");
  m<<QVariant::fromValue(keyTemplate())<<QVariant::fromValue(pairParams())<<QVariant::fromValue(kdfParams(rounds[index]))<<QVariantMap()<<QString("org.sailfishos.secrets.plugin.encryptedstorage.sqlcipher");
  QDBusMessage reply=connection.call(m,QDBus::Block,15000);
  QJsonObject record{{"iterations",rounds[index]},{"provider",QString("SQLCipher")},{"persistent_request",false}};
  if(reply.type()!=QDBusMessage::ReplyMessage || reply.arguments().size()!=2){record.insert("invalid_reply",true);output(record);return 2;}
  const QDBusArgument result=qvariant_cast<QDBusArgument>(reply.arguments()[0]);
  if(result.currentSignature()!="(iiis)"){record.insert("unexpected_result_schema",true);output(record);return 2;}
  int code=0,error=0,storageError=0;QString ignoredError;
  result.beginStructure();result>>code>>error>>storageError>>ignoredError;result.endStructure();
  record.insert("result",code);record.insert("error",error);record.insert("storage_error",storageError);
  if(code!=0){output(record);return 2;}
  const QDBusArgument key=qvariant_cast<QDBusArgument>(reply.arguments()[1]);
  if(key.currentSignature()!="((sss)iiiiiayayayaay(a{sv}))"){record.insert("unexpected_key_schema",true);output(record);return 2;}
  QString name,collection,plugin;int origin=0,algorithm=0,operations=0,constraints=0,size=0;
  QByteArray publicKey,privateKey,secretKey;QList<QByteArray> custom;QVariantMap filters;
  key.beginStructure();key.beginStructure();key>>name>>collection>>plugin;key.endStructure();
  key>>origin>>algorithm>>operations>>constraints>>size>>publicKey>>privateKey>>secretKey>>custom;
  key.beginStructure();key>>filters;key.endStructure();key.endStructure();
  bool matches=name.isEmpty() && collection.isEmpty() && plugin.isEmpty() && publicKey.isEmpty() && privateKey.isEmpty()
    && algorithm==260 && size==256 && secretKey.size()==32 && secretKey==QByteArray::fromHex(expected[index]);
  record.insert("derived_bytes",secretKey.size());record.insert("public_vector_match",matches);output(record);
  if(!matches)return 3;
 }
 QDBusConnection::disconnectFromPeer("synthetic-kdf-capability");return 0;
}
