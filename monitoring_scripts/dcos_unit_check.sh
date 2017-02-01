# cat dcos_unit_check.sh
#!/bin/bash
for unit in `ls /etc/systemd/system/dcos.target.wants`; do
  echo "Checking $unit"
  /usr/bin/check_service.sh -o linux -s ${unit} > /dev/null 2>&1
  STATUS=$?
  if [ "${STATUS}" -ne 0 ]; then
    echo "Status for $unit is not 0, got $STATUS"
    exit $STATUS
  fi
done
