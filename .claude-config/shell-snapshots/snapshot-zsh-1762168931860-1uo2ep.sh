# Snapshot file
# Unset all aliases to avoid conflicts with functions
unalias -a 2>/dev/null || true
# Functions
conda () {
	if [ "$#" -lt 1 ]
	then
		"$CONDA_EXE" $_CE_M $_CE_CONDA
	else
		\local cmd="$1"
		shift
		case "$cmd" in
			(activate | deactivate) __conda_activate "$cmd" "$@" ;;
			(install | update | upgrade | remove | uninstall) CONDA_INTERNAL_OLDPATH="${PATH}" 
				__add_sys_prefix_to_path
				"$CONDA_EXE" $_CE_M $_CE_CONDA "$cmd" "$@"
				\local t1=$?
				PATH="${CONDA_INTERNAL_OLDPATH}" 
				if [ $t1 = 0 ]
				then
					__conda_reactivate
				else
					return $t1
				fi ;;
			(*) CONDA_INTERNAL_OLDPATH="${PATH}" 
				__add_sys_prefix_to_path
				"$CONDA_EXE" $_CE_M $_CE_CONDA "$cmd" "$@"
				\local t1=$?
				PATH="${CONDA_INTERNAL_OLDPATH}" 
				return $t1 ;;
		esac
	fi
}
pyenv () {
	local command=${1:-} 
	[ "$#" -gt 0 ] && shift
	case "$command" in
		(rehash | shell) eval "$(pyenv "sh-$command" "$@")" ;;
		(*) command pyenv "$command" "$@" ;;
	esac
}
# Shell Options
setopt nohashdirs
setopt login
# Aliases
alias -- run-help=man
alias -- which-command=whence
# Check for rg availability
if ! command -v rg >/dev/null 2>&1; then
  alias rg='/opt/homebrew/lib/node_modules/\@anthropic-ai/claude-code/vendor/ripgrep/arm64-darwin/rg'
fi
export PATH=/Users/scottmcguire/.pyenv/versions/3.13.5/bin\:/opt/homebrew/Cellar/pyenv/2.6.11/libexec\:/opt/homebrew/Cellar/pyenv/2.6.11/plugins/python-build/bin\:/usr/local/bin\:/System/Cryptexes/App/usr/bin\:/usr/bin\:/bin\:/usr/sbin\:/sbin\:/var/run/com.apple.security.cryptexd/codex.system/bootstrap/usr/local/bin\:/var/run/com.apple.security.cryptexd/codex.system/bootstrap/usr/bin\:/var/run/com.apple.security.cryptexd/codex.system/bootstrap/usr/appleinternal/bin\:/Library/Apple/usr/bin\:/var/folders/6y/g75y8h_s1ws2809fn5yd_kmr0000gn/T/.tmpvmWvSx\:/opt/homebrew/lib/node_modules/\@openai/codex/vendor/aarch64-apple-darwin/path\:/Users/scottmcguire/.opencode/bin\:/Users/scottmcguire/.pyenv/shims\:/opt/anaconda3/bin\:/opt/anaconda3/condabin\:/opt/homebrew/bin\:/opt/homebrew/sbin\:/Applications/Ghostty.app/Contents/MacOS
