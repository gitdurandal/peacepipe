#!/bin/bash
# peacepipe 0.2.2  - 2013/08/08
#
#
# COPYRIGHT
###########
# peacepipe is Copyright (c) Jason Thistlethwaite 2013 (iadnah@uplinklounge.com)
#
#    peacepipe is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 2 of the License, or
#    (at your option) any later version.
#
#    peacepipe is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with peacepipe.  If not, see <http://www.gnu.org/licenses/>.
#
##########

##
# Configuration Variables
# Variables which configure how peacepipe behaves
##

 # Max recursion depth
 readonly MAXLOOPS=${MAXLOOPS:-255}

 # Maximum file size (in bytes) for pre-processing
 # Files larger than this will not be pre-processed
 # Setting this too high can result in runaway apache processes
 readonly MAXSIZE=${MAXSIZE:-20971520}

 errContentType="text/html"

##
# Runtime state variables
# Variables which track state during runtime
##

 # If non-zero operate in "raw/download" mode
 #  1) Determine the mimetype of the requested file
 #  2) Send the appropriate Content-Type header
 #  3) Read the file to the client and exit
 OUTPUT_RAW=${OUTPUT_RAW:-0}

 # Source highlighting.
 # If non-zero source files will be highlighted
 OUTPUT_HL=${OUTPUT_HL:-0}


 # Have we sent headers to the client yet?
 export HEADERS_SENT=0


 # Full pathname to the local file being requested
 FILE=${PATH_TRANSLATED:-""}

 # The QUERY_STRING (everything after '?' in the URL)
 QUERY=${QUERY_STRING:-""}


 # Content-Type header to send the browser
 # Should be set to a reasonable default (text/plain)
 contentType=${contentType:-"text/plain"}

 # If non-zero error messages will include HTML when applicable
 HTMLERRORS=1

 readonly errContentType=${errContentType:-"$contentType"}

##
# Function Declarations
##

##
# Exit and display an error to the user
# @param mixed|string Message to show the user
##
exitErr() {
	wprint "Cannot serve $FILE"
	wprint "$@"
	exit 1
}

##
# Send output to the browser.
#
# Send output to the browser, generally text or HTML. Sends errContentType as Content-Type header
# the first time it is called.
#
# @param mixed|string String to output to the browser
# @return integer Returns 0 on success
##
wprint() {
	if [ ${HEADERS_SENT} = 0 ]; then
		echo -e "Content-Type: ${errContentType}\r\n\r\n"
		HEADERS_SENT=1
	fi
	echo "$@"
	return $?
}

##
# parse a QUERY_STRING
#
#
##
parseQuery()
{
	# Check if there is a query string and parse it
	if [ "${QUERY}x" != "x" ]; then
		loops=0
		tok=""
		while [ "${QUERY[0]}" != "${tok}" ]; do
			tok="${QUERY%\&*}"
			tok="${QUERY##*\&}"
			QUERY="${QUERY%\&*}"

			case "$tok" in
				# Don't pre-process the file at all.
				# Just set the correct content-type and send the raw data for download
				"dl"|"raw")
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
}

parseQuery

# Process the requested file (if accessible)
if [ -a "${FILE}" ]; then
	bfilename=$(basename "$FILE")	# basename of the requested file
	extension="${FILE##*.}"		# file extension of requested file
	filename="${FILE%.*}"		# basename without extension
	filesize=`stat -c %s ${FILE}`	# Get size of file (in bytes)

	if [ "${OUTPUT_RAW}" = "1" ]; then
		contentType=`file --mime "${FILE}" | awk '{print $2}' | sed -e "s/;//"`
		echo -e "Content-Type: $contentType\r\n\r\n"
		cat "${FILE}"
		exit 0
	fi

	if [[ $filesize -gt $MAXSIZE ]]; then
		if [[ $HTMLERRORS -eq 1 ]]; then
			exitErr "<br />Filesize ($filesize) exceeds maximum ($MAXSIZE): <a href='?dl'>[Download File]</a>"
			exit 1

		else
			exitErr "Filesize ($filesize) exceeds maximum ($MAXSIZE): Download File: [Download File]"
			exit 1
		fi
		exit 1
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
