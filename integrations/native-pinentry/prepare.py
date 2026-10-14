#!/usr/bin/env python3
"""Prepare a cache-free experimental build of pinned Sailfish native pinentry."""
import difflib,hashlib,json
from pathlib import Path
root=Path(__file__).resolve().parent
out=root/'prepared';out.mkdir(exist_ok=True)
cpp=(root/'upstream/qassuanserver.cpp').read_text();original=cpp
for header in ['storesecretrequest','storedsecretrequest','createcollectionrequest']:
 cpp=cpp.replace('#include <Secrets/'+header+'.h>\n','')
cpp=cpp.replace('    self->cacheId.setName(QString());\n','')
start=cpp.index('    // Ugly hack here')
end=cpp.index('    return 0;',start)
cpp=cpp[:start]+cpp[end:]
cpp=cpp.replace('    self->cacheId.setName((*line && strcmp(line, "--clear") !=0) ? line : QString());','    Q_UNUSED(self); Q_UNUSED(line); // No external cache in this UI-only proof.')
start=cpp.index('    if (self->cacheId.isValid()) {');end=cpp.index('    gpg_error_t rc =',start)
cpp=cpp[:start]+cpp[end:]
cpp=cpp.replace('    , m_useCache(new MDConfItem("/desktop/sailfish/secrets/storeGnuPGPassphrases", this))\n','')
cpp=cpp.replace('    cacheId.setCollectionName(QStringLiteral("GnuPG"));\n','').replace('    cacheId.setStoragePluginName(Sailfish::Secrets::SecretManager::DefaultEncryptedStoragePluginName);\n','')
start=cpp.index('    bool useCache =');end=cpp.index('    Sailfish::Secrets::InteractionParameters uiParams;',start)
cpp=cpp[:start]+cpp[end:]
start=cpp.index('        if (useCache &&');end=cpp.index('\n    }\n\n    return request.result();',start)
cpp=cpp[:start]+cpp[end:]
cpp=cpp[:cpp.index('\nbool QAssuanServer::ensureCacheCollection()')]
# Modern libassuan uses libgpg-error values and typed unsigned callbacks.
cpp=cpp.replace('typedef int (*OptionHandler)', 'typedef gpg_error_t (*OptionHandler)').replace('typedef int (*CmdHandler)', 'typedef gpg_error_t (*CmdHandler)').replace('    int (*handler)', '    gpg_error_t (*handler)')
for old,new in {'Not_Implemented':'gpg_error(GPG_ERR_NOT_IMPLEMENTED)','Invalid_Option':'gpg_error(GPG_ERR_UNKNOWN_OPTION)','Canceled':'gpg_error(GPG_ERR_CANCELED)','General_Error':'gpg_error(GPG_ERR_GENERAL)','Parameter_Error':'gpg_error(GPG_ERR_INV_VALUE)','No_Error':'0'}.items():
 cpp=cpp.replace('ASSUAN_'+old,new)
cpp=cpp.replace('assuan_register_command(ctx, table[i].name, table[i].handler)', 'assuan_register_command(ctx, table[i].name, table[i].handler, nullptr)')
cpp=cpp.replace('void _reset_handler(assuan_context_t ctx)', 'gpg_error_t _reset_handler(assuan_context_t ctx, char *line)')
cpp=cpp.replace('    self->prompt = Sailfish::Secrets::InteractionParameters::PromptText();', '    Q_UNUSED(line);\n    self->prompt = Sailfish::Secrets::InteractionParameters::PromptText();\n    return 0;')
cpp=cpp.replace('rc = assuan_init_pipe_server(&m_ctx, filedesc);', 'rc = assuan_new(&m_ctx);\n    if (!rc) rc = assuan_init_pipe_server(m_ctx, filedesc);')
cpp=cpp.replace('assuan_deinit_server(m_ctx)', 'assuan_release(m_ctx)')
cpp=cpp.replace('    , m_connected(false)', '    , m_connected(false)\n    , m_ctx(nullptr)')
cpp=cpp.replace('    m_connected = true;\n', '')
cpp=cpp.replace('assuan_release(m_ctx);\n        return;', 'assuan_release(m_ctx);\n        m_ctx = nullptr;\n        return;')
cpp=cpp.replace('<< gpg_strerror(rc);\n        return;', '<< gpg_strerror(rc);\n        if (m_ctx) assuan_release(m_ctx);\n        m_ctx = nullptr;\n        return;')
cpp=cpp.replace('\n}\n\nQAssuanServer::~QAssuanServer()', '\n    m_connected = true;\n}\n\nQAssuanServer::~QAssuanServer()')
cpp=cpp.replace('void QAssuanServer::start()', 'bool QAssuanServer::start()').replace('if (!m_connected) {\n        return;', 'if (!m_connected) {\n        return false;').replace('    QThread::start();', '    QThread::start();\n    return true;')
cpp=cpp.replace('if (rc == -1)', 'if (rc == static_cast<gpg_error_t>(-1))')
cpp=cpp.replace('assuan_error_t rc;', 'gpg_error_t rc;').replace('assuan_strerror(rc)', 'gpg_strerror(rc)')
# This process has no Secrets storage/cache path, so acknowledge permission without using it.
cpp=cpp.replace('!strcmp(key, "allow-external-password-cache") && !*value) {\n        return gpg_error(GPG_ERR_NOT_IMPLEMENTED);', '!strcmp(key, "allow-external-password-cache") && !*value) {\n        return 0; // Persistence is unconditionally disabled in this build.')
# GnuPG accepts NOT_SUPPORTED for optional no-grab; NOT_IMPLEMENTED is fatal.
cpp=cpp.replace('!strcmp(key, "no-grab") && !*value) {\n        return gpg_error(GPG_ERR_NOT_IMPLEMENTED);', '!strcmp(key, "no-grab") && !*value) {\n        return gpg_error(GPG_ERR_NOT_SUPPORTED);')
# Suppress upstream descriptions/identifier/error details in diagnostic output.
cpp=cpp.replace('<< key << value','<< key').replace('<< __func__ << line','<< __func__')
cpp=cpp.replace('<< result.errorMessage()', '<< result.errorCode()').replace('<< request.result().errorMessage()', '<< request.result().errorCode()')
assert not any(token in cpp for token in ['StoreSecretRequest','StoredSecretRequest','CreateCollectionRequest','MDConfItem','PASSWORD_FROM_CACHE','cacheId'])
(out/'qassuanserver.cpp').write_text(cpp)
h=(root/'upstream/qassuanserver.h').read_text().replace('#include <MDConfItem>\n','').replace('    Sailfish::Secrets::Secret::Identifier cacheId;\n','').replace('    MDConfItem *m_useCache;\n','').replace('    bool ensureCacheCollection();\n','').replace('friend void _reset_handler(assuan_context_t);', 'friend gpg_error_t _reset_handler(assuan_context_t, char *);').replace('    void start();','    bool start();')
(out/'qassuanserver.h').write_text(h)
main=(root/'upstream/pinentry.cpp').read_text().replace('#include <QCoreApplication>', '#include <QCoreApplication>\n#include <unistd.h>')
main=main.replace('    Pinentry pin(argc, argv);', '    alarm(120); // Bound the UI-only synthetic helper lifetime, including stalled IPC.\n    Pinentry pin(argc, argv);')
main=main.replace('    server.start();', '    if (!server.start()) return 1;')
(out/'pinentry.cpp').write_text(main)
(root/'cache-free-modern-assuan.patch').write_text(''.join(difflib.unified_diff(original.splitlines(True),cpp.splitlines(True),fromfile='a/qassuanserver.cpp',tofile='b/qassuanserver.cpp'))+''.join(difflib.unified_diff((root/'upstream/qassuanserver.h').read_text().splitlines(True),h.splitlines(True),fromfile='a/qassuanserver.h',tofile='b/qassuanserver.h')))
(out/'pinentry.pro').write_text('''TEMPLATE = app
TARGET = pinentry
QT -= gui
QT += core dbus
CONFIG += link_pkgconfig c++11
PKGCONFIG += sailfishsecrets
INCLUDEPATH += /usr/include/Sailfish /home/ubuntu/gnupg-runtime/build/libassuan-3.0.2-build/src /home/ubuntu/gnupg-runtime/build/libgpg-error-1.61-build/src
LIBS += /home/ubuntu/gnupg-runtime/build/stage/usr/libexec/sailfish-gnupg/lib/libassuan.so.9 /home/ubuntu/gnupg-runtime/build/stage/usr/libexec/sailfish-gnupg/lib/libgpg-error.so.0
QMAKE_LFLAGS += -Wl,-rpath,/usr/libexec/sailfish-gnupg/lib
HEADERS += qassuanserver.h
SOURCES += qassuanserver.cpp pinentry.cpp
''')
record={'upstream_commit':'5a8d33e2eda2fe10a64acc42912dd3bedc736495','files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (root/'upstream').iterdir()},'scope':'UI-only synthetic prototype; no persistent-cache operations; unchanged GnuPG'}
(root/'sources.json').write_text(json.dumps(record,indent=2)+'\n')
print('PASS: prepared native pinentry with no persistent storage path')

with (root/'cache-free-modern-assuan.patch').open('a') as f:
 f.write(''.join(difflib.unified_diff((root/'upstream/pinentry.cpp').read_text().splitlines(True),main.splitlines(True),fromfile='a/pinentry.cpp',tofile='b/pinentry.cpp')))
