/**
 * W3F Web Index Survey - Angular interface to Google Spreadsheets
 *
 * Copyright (C) 2014  Ben Doherty @ Oomph, Inc.
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */
angular.module("GoogleSpreadsheets", []).factory("spreadsheets", [
  "$http",
  "$q",
  "$cookies",
  function ($http, $q, $cookies) {
    var service = this


    var getText = function (entry, field) {
      var elements = entry.getElementsByTagName(field)

      if (elements.length > 0) {
        return elements[0].textContent
      } else {
        return null
      }
    }

    // Introduce an "abort" method on promise objects which will
    // kill the current request
    var defer = function () {
      var deferred = $q.defer()

      deferred.promise.abort = function () {
        deferred.reject("cancelled")
      }

      return deferred
    }

    // Process a single XML entry for a list feed and return a "row"
    var mungeEntry = function (entry) {
      var id = entry.getElementsByTagName("id")
      var cells = entry.getElementsByTagNameNS(
        "http://schemas.google.com/spreadsheets/2006/extended",
        "*"
      )
      var key
      var row = {}

      angular.forEach(cells, function (cell) {
        var col = cell.tagName.match(/^gsx:(.+)$/)[1]

        row[col] = cell.textContent
      })

      var links = entry.getElementsByTagName("link")

      // Prefix meta data with :, save links and row id
      row[":links"] = {}

      angular.forEach(links, function (link) {
        row[":links"][link.getAttribute("rel")] = link.getAttribute("href")
      })

      row[":id"] = id[0].textContent.match(/\/([^\/]+)$/)[1]

      return row
    }

    function getSheets(key) {
      var deferred = defer()

      var url = '/api/survey/'+ key + '/data/'

      if (key == 'questions') {
        url = '/api/question-data/'
      }

      $http({
        method: "GET",
        url: url,
        timeout: deferred,
      })
        .then(function (response) {
          deferred.resolve(response.data)
        })
        .then(function (error) {
          deferred.reject("Unable to access answer data.")
        })

      return deferred.promise
    }

    function getRows(sheet, useKey) {
      var rows = useKey ? {} : []

      angular.forEach(sheet.data, function (row) {
        if (useKey) {
          rows[row[useKey]] = row
        } else {
          rows.push(row)
        }
      })
      return rows
    }

    function updateRow(url, values) {
      var deferred = defer()

      $http({
        method: "PUT",
        url: url,
        headers: {
          'X-CSRFToken': $cookies.csrftoken,
        },
        timeout: deferred,
        data: values,
      })
        .then(function (response) {
          deferred.resolve(response.data)
        })
        .then(function (error) {
          // Don't necessarily call 409 status an error: maybe nothing was going to change
          // anyway
          if (status == 409) {
            deferred.resolve(error)
          }

          deferred.reject(error)
        })

      return deferred.promise
    }

    function insertRow(sheet, values) {
      var url =
        "https://spreadsheets.google.com/feeds/list/" +
        sheet.key +
        "/" +
        sheet.id +
        "/private/full"
      var deferred = defer()

      $http({
        method: "POST",
        url:
          "/google-spreadsheets.php?action=submit&url=" + url + "&method=POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
        timeout: deferred,
        data: $.param(values),
      })
        .then(function (response) {
          var xml = new DOMParser().parseFromString(response.data, "text/xml")
          var entries = xml.getElementsByTagName("entry")

          deferred.resolve(mungeEntry(entries[0]))
        })
        .then(function (error) {
          deferred.reject(error)
        })

      return deferred.promise
    }

    function deleteRow(url, id) {

      var deferred = defer()

      $http({
        method: "GET",
        url:
          "/google-spreadsheets.php?action=submit&url=" +
          url +
          "&method=DELETE",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
        timeout: deferred,
      })
        .then(function (response) {
          var xml = new DOMParser().parseFromString(response.data, "text/xml")
          var entries = xml.getElementsByTagName("entry")
          deferred.resolve({ id: id })
        })
        .then(function (error) {
          deferred.reject(error)
        })

      return deferred.promise
    }

    function updateUpload(sheet, upload) {
      var deferred = defer()

      getRows(sheet.key, sheet).then(function (uploads) {
        var url;
        angular.forEach(uploads, function (resource) {
          if (resource.id === upload.id) {
            url = resource[':links'].edit
          }
        })
        var parseResponse = function (data) {
          var xml = new DOMParser().parseFromString(data, "text/xml")
          var entries = xml.getElementsByTagName("entry")

          return mungeEntry(entries[0])
        }

        $http({
          method: "POST",
          url:
            "/google-spreadsheets.php?action=submit&url=" + url + "&method=PUT",
          headers: {
            "Content-Type": "application/x-www-form-urlencoded",
          },
          timeout: deferred,
          data: $.param(upload),
        })
          .then(function (response) {
            deferred.resolve(parseResponse(response.data))
          })
          .then(function (error) {
            // Don't necessarily call 409 status an error: maybe nothing was going to change
            // anyway
            if (status == 409) {
              deferred.resolve(parseResponse(error))
            }

            deferred.reject(error)
          })
      })
      return deferred.promise
    }

    function deleteUpload(sheet, id) {

      var deferred = defer()

      getRows(sheet.key, sheet).then(function (uploads) {
        var url;
        angular.forEach(uploads, function (upload) {
          if (upload.id === id) {
            url = upload[':links'].edit
          }
        })
        $http({
          method: "GET",
          url:
            "/google-spreadsheets.php?action=submit&url=" +
            url +
            "&method=DELETE",
          headers: {
            "Content-Type": "application/x-www-form-urlencoded",
          },
          timeout: deferred,
        })
          .then(function (response) {
            deferred.resolve({ id: id })
          })
          .then(function (error) {
            deferred.reject(error)
          })
      })
      return deferred.promise
    }

    return {
      getSheets: getSheets,
      getRows: getRows,
      updateRow: updateRow,
      insertRow: insertRow,
      deleteRow: deleteRow,
      deleteUpload: deleteUpload,
      updateUpload: updateUpload,
    }
  },
])
