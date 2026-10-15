# Sourced only by the fixed BusyBox entry wrappers. No caller-controlled paths.
private_prefix=/usr/libexec/sailfish-gnupg
proc_root=/proc
current_uid=$(/usr/bin/id -u)
if test -x /bin/stat; then stat_tool=/bin/stat; else stat_tool=/usr/bin/stat; fi

policy_error() { echo "$1" >&2; return 78; }

runtime_exec() {
    /usr/bin/env -i PATH=/usr/bin:/bin HOME="$SAILFISH_GNUPGHOME" \
        LANG="${LANG:-C}" LC_ALL="${LC_ALL:-}" TERM="${TERM:-dumb}" \
        GPG_TTY="${GPG_TTY:-}" XDG_RUNTIME_DIR="/run/user/$current_uid" \
        GNUPGHOME="$SAILFISH_GNUPGHOME" "$@"
}

# Start time and parent identity keep a reused PID out of our timeout cleanup.
# These are public kernel metadata for subprocesses started by this wrapper.
policy_process_identity() {
    process_stat=$(/usr/bin/busybox cat "/proc/$1/stat") || return 1
    process_stat=${process_stat##*) }
    set -- $process_stat
    test "$#" -ge 20 || return 1
    process_parent=$2
    shift 19
    process_identity="$process_parent:$1"
}

# Own the IPC and its watchdog in a separate process. If the calling wrapper
# disappears, their parent identity remains stable until bounded cleanup finishes.
# This supervises one direct IPC helper, not arbitrary daemon descendants.
runtime_timed() {
    ( runtime_timed_supervised "$@" ) &
    supervisor_pid=$!
    if wait "$supervisor_pid"; then return 0; else return "$?"; fi
}

runtime_timed_supervised() {
    (
        exec /usr/bin/env -i PATH=/usr/bin:/bin HOME="$SAILFISH_GNUPGHOME" \
            LANG="${LANG:-C}" LC_ALL="${LC_ALL:-}" TERM="${TERM:-dumb}" \
            GPG_TTY="${GPG_TTY:-}" XDG_RUNTIME_DIR="/run/user/$current_uid" \
            GNUPGHOME="$SAILFISH_GNUPGHOME" "$@"
    ) &
    ipc_pid=$!
    if policy_process_identity "$ipc_pid"; then ipc_identity=$process_identity; else ipc_identity=; fi
    (
        watchdog_cancelled=0
        watchdog_result=0
        trap 'watchdog_cancelled=1' TERM INT
        /usr/bin/busybox sleep 15 &
        sleeper_pid=$!
        if policy_process_identity "$sleeper_pid"; then sleeper_identity=$process_identity; else sleeper_identity=; fi
        if test "$watchdog_cancelled" = 0; then wait "$sleeper_pid" || :; fi
        if test -n "$sleeper_identity" && policy_process_identity "$sleeper_pid" 2>/dev/null && test "$process_identity" = "$sleeper_identity"; then
            kill -KILL "$sleeper_pid" 2>/dev/null || :
        fi
        wait "$sleeper_pid" 2>/dev/null || :
        if test "$watchdog_cancelled" = 0 && test -n "$ipc_identity" && policy_process_identity "$ipc_pid" 2>/dev/null && test "$process_identity" = "$ipc_identity"; then
            watchdog_result=124
            kill -TERM "$ipc_pid" 2>/dev/null || :
            /usr/bin/busybox sleep 1
            if test "$watchdog_cancelled" = 0 && policy_process_identity "$ipc_pid" 2>/dev/null && test "$process_identity" = "$ipc_identity"; then
                kill -KILL "$ipc_pid" 2>/dev/null || :
            fi
        fi
        exit "$watchdog_result"
    ) &
    watchdog_pid=$!
    if policy_process_identity "$watchdog_pid"; then watchdog_identity=$process_identity; else watchdog_identity=; fi
    if wait "$ipc_pid"; then ipc_result=0; else ipc_result=$?; fi
    if test -n "$watchdog_identity" && policy_process_identity "$watchdog_pid" 2>/dev/null && test "$process_identity" = "$watchdog_identity"; then
        kill -TERM "$watchdog_pid" 2>/dev/null || :
    fi
    if wait "$watchdog_pid" 2>/dev/null; then watchdog_result=0; else watchdog_result=$?; fi
    # A helper's apparent success after timeout (including emulated execution)
    # must never turn a timed-out IPC request into successful admission.
    case "$watchdog_result" in
        0) return "$ipc_result" ;;
        124) return 124 ;;
        *) return 78 ;;
    esac
}

policy_home() {
    case ${SAILFISH_GNUPGHOME:-} in /*) ;; *) return 64 ;; esac
    test -d "$SAILFISH_GNUPGHOME" && test ! -L "$SAILFISH_GNUPGHOME" || return 64
    test "$("$stat_tool" -c '%u %a' "$SAILFISH_GNUPGHOME")" = "$current_uid 700" || return 64
    physical_home=$(command cd -P "$SAILFISH_GNUPGHOME" && command pwd -P) || return 64
    test "$physical_home" = "$SAILFISH_GNUPGHOME" || return 64

    # Query public account metadata, never a key or password-store file.
    account_record=$(/usr/bin/getent passwd "$current_uid") || return 64
    IFS=: read -r account_name account_password account_uid account_gid account_gecos account_home account_shell <<EOF
$account_record
EOF
    test "$account_uid" = "$current_uid" || return 64
    case "$account_home" in /*) ;; *) return 64 ;; esac
    account_home=$(command cd -P "$account_home" && command pwd -P) || return 64
    stock_home="$account_home/.gnupg"
    if test -e "$stock_home" || test -L "$stock_home"; then
        stock_home=$(command cd -P "$stock_home" && command pwd -P) || return 64
    fi
    case "$SAILFISH_GNUPGHOME/" in "$stock_home/"*)
        echo 'The account default GnuPG home cannot be used' >&2; return 64 ;; esac
    case "$stock_home/" in "$SAILFISH_GNUPGHOME/"*)
        echo 'The private home must not contain the account default GnuPG home' >&2; return 64 ;; esac

    # No configuration contents are read, altered or silently adopted.
    # Also reject version suffixes and system gpg.conf: system [force] options
    # survive --no-options in the pinned libgpg-error parser.
    for configuration in "$SAILFISH_GNUPGHOME/common.conf"* \
        "$SAILFISH_GNUPGHOME/gpg-agent.conf"* \
        "$private_prefix/etc/gnupg/common.conf"* \
        "$private_prefix/etc/gnupg/gpg-agent.conf"* \
        "$private_prefix/etc/gnupg/gpg.conf"* \
        "$private_prefix/bin/gpgconf.ctl"; do
        if test -e "$configuration" || test -L "$configuration"; then
            policy_error 'Private CLI requires absent common/agent/relocation configuration'
            return 78
        fi
    done
}

policy_verify_agent() {
    case "$agent_pid" in ''|0|*[!0-9]*) policy_error 'Invalid agent PID'; return 78 ;; esac
    test "$("$stat_tool" -c %u "$proc_root/$agent_pid")" = "$current_uid" || return 78
    test "$(/usr/bin/busybox readlink "$proc_root/$agent_pid/exe")" = "$private_prefix/bin/gpg-agent" || {
        policy_error 'Agent executable is not the current private runtime'; return 78;
    }
    test "$("$stat_tool" -Lc '%d:%i' "$proc_root/$agent_pid/exe")" = \
         "$("$stat_tool" -Lc '%d:%i' "$private_prefix/bin/gpg-agent")" || return 78

    # Accept only the exact launch argv generated by the private IPC launcher.
    argument_number=0
    while IFS= read -r -d '' argument; do
        argument_number=$((argument_number + 1))
        case "$argument_number:$argument" in
            "1:$private_prefix/bin/gpg-agent"|"1:gpg-agent"|"2:--homedir"|\
            "3:$SAILFISH_GNUPGHOME"|"4:--no-options"|"5:--daemon") ;;
            *) policy_error 'Agent launch options do not match the managed runtime'; return 78 ;;
        esac
    done < "$proc_root/$agent_pid/cmdline"
    test "$argument_number" = 5 || return 78

    found_gcrypt=0; found_assuan=0; found_error=0; found_npth=0
    while read -r address permissions offset device inode mapped remainder; do
        case "$mapped" in
            "$private_prefix/"*)
                test -z "$remainder" || { policy_error 'Agent has obsolete private mappings'; return 78; }
                test "$inode" = "$("$stat_tool" -c %i "$mapped")" || return 78 ;;
        esac
        case "$mapped" in
            */libgcrypt.so*) soname=libgcrypt.so.20; found_gcrypt=1 ;;
            */libassuan.so*) soname=libassuan.so.9; found_assuan=1 ;;
            */libgpg-error.so*) soname=libgpg-error.so.0; found_error=1 ;;
            */libnpth.so*) soname=libnpth.so.0; found_npth=1 ;;
            *) continue ;;
        esac
        test -z "$remainder" && test "$mapped" = \
            "$(/usr/bin/busybox readlink -f "$private_prefix/lib/$soname")" || {
            policy_error 'Agent crypto library is outside the current private runtime'; return 78;
        }
    done < "$proc_root/$agent_pid/maps"
    test "$found_gcrypt$found_assuan$found_error$found_npth" = 1111 || return 78
}

# Return 3 only for an absent socket. IPC exit0 without PID is not acceptance.
policy_agent_status() {
    agent_socket=$(runtime_exec "$private_prefix/bin/gpgconf" --homedir "$SAILFISH_GNUPGHOME" --list-dirs agent-socket) || return 78
    case "$agent_socket" in /*) ;; *) return 78 ;; esac
    if test ! -e "$agent_socket" && test ! -L "$agent_socket"; then return 3; fi
    test -S "$agent_socket" && test ! -L "$agent_socket" || return 78
    test "$("$stat_tool" -c '%u %a' "$agent_socket")" = "$current_uid 700" || return 78
    socket_parent=${agent_socket%/*}
    test "$(command cd -P "$socket_parent" && command pwd -P)" = "$socket_parent" || return 78
    test "$("$stat_tool" -c '%u %a' "$socket_parent")" = "$current_uid 700" || return 78
    agent_reply=$(runtime_timed \
        "$private_prefix/bin/gpg-connect-agent" --no-history --homedir "$SAILFISH_GNUPGHOME" \
        --raw-socket "$agent_socket" 'GETINFO pid' /bye) || return 78
    case "$agent_reply" in
        'D '*'
OK') agent_pid=${agent_reply#D }; agent_pid=${agent_pid%'
OK'} ;;
        *) policy_error 'Agent PID response missing or malformed'; return 78 ;;
    esac
    policy_verify_agent
}

policy_ensure_agent() {
    if policy_agent_status; then :; else
        agent_state=$?
        test "$agent_state" = 3 || return "$agent_state"
        runtime_timed "$private_prefix/bin/gpg-connect-agent" \
            --no-history --homedir "$SAILFISH_GNUPGHOME" \
            --agent-program "$private_prefix/bin/gpg-agent|--no-options" 'GETINFO pid' /bye >/dev/null || return 78
        policy_agent_status || return 78
    fi
}

policy_report_agent() {
    case ${SAILFISH_LIFECYCLE_REPORT_FD:-} in ''|*[!0-9]*) return 78 ;; esac
    policy_process_identity "$agent_pid" || return 78
    printf '%s %s\n' "$agent_pid" "${process_identity#*:}" >&"$SAILFISH_LIFECYCLE_REPORT_FD"
}
