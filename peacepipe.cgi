#!/bin/bash
export HEADERS_SENT=0

exitErr() {
	wprint "Cannot serve $FILE"
	wprint "$@"
	exit 1
}

wprint() {
	if [ ${HEADERS_SENT} = 0 ]; then
		echo -e "Content-Type: text/plain\r\n\r\n"
		HEADERS_SENT=1
	fi
	echo "$@"
	return 0
}

FILE=${PATH_TRANSLATED:-""}
QUERY=${QUERY_STRING:-""}

readonly MAXLOOPS=255
OUTPUT_RAW=0
OUTPUT_HL=0
contentType="text/plain"

if [ "${QUERY}x" != "x" ]; then
	loops=0
	tok=""
	while [ "${QUERY[0]}" != "${tok}" ]; do
		tok="${QUERY%\&*}"
		tok="${QUERY##*\&}"
		QUERY="${QUERY%\&*}"

		case "$tok" in
			"raw")
				OUTPUT_RAW=1
			;;
			'hl')
				OUTPUT_HL=1
			;;
			*)
		esac

		((loops++))

		if (( $loops > $MAXLOOPS )); then
			exitErr "We got too loopy"
		fi
	done
	loops=0
fi

if [ -a "${FILE}" ]; then
	bfilename=$(basename "$FILE")
	extension="${FILE##*.}"
	filename="${FILE%.*}"

	if [ "${OUTPUT_RAW}" = "1" ]; then
		contentType=`file --mime "${FILE}" | awk '{print $2}' | sed -e "s/;//"`
		echo -e "Content-Type: $contentType\r\n\r\n"
		cat "${FILE}"
		exit 0
	fi

	case `echo "$extension" | tr '[:upper:]' '[:lower:]'` in
                        bz2|gz|tgz|zip|tar)
				subextension="${filename##*.}"
				outputPipe=""

				case `echo "$extension" | tr '[:upper:]' '[:lower:]'` in
					bz2) OPENCMD="bunzip2 -dc" ;;
					gz) OPENCMD="gunzip -dc" ;;
					tgz) OPENCMD="gunzip -dc";
						subextension="tar";;
					zip) OPENCMD="unzip -v";;
					tar) OPENCMD="cat"
						subextension="tar";;

					*)
						exitErr "We don't know what to do here";;
				esac

				case "$subextension" in
					1|2|3|4|5|6|7|8|9)
						contentType=""
						outputPipe="man2html -r -H killdozer.da.hephaestussec.com"
					;;

					tar)
						contentType="text/plain"
						outputPipe="tar -tvf -"
					;;

					*)

				esac
				if [ "${contentType}x" != "x" ]; then
					echo -e "Content-Type: $contentType\r\n\r\n"
				fi

				if [ "${outputPipe}x" = "x" ]; then
					${OPENCMD} "$FILE"
				else
					${OPENCMD} "$FILE" | ${outputPipe}
				fi
				exit 0
			;;

			1|2|3|4|5|6|7|8|9)
	                        contentType=""
                                cat "$FILE" | man2html -r -H killdozer.da.hephaestussec.com
				exit 0
				;;

			c|cpp|h|sh|pl|pm|py|diff|vb|vbs|php)
				echo -e "Content-Type: text/html\r\n\r\n"
				cat "$FILE" | highlight --inline-css --line-number=4 --failsafe -S "${extension}" \
					-O html --anchors -s night --line-number-ref -T "${bfilename}"

				echo "We are here with $FILE" 1>&2

				exit 0
			;;


		*)
				exitErr "Unsupported file format $extension for $filename"
				;;

	esac


else
	exitErr "File doesn't exist"
fi
