apiVersion: resource-management.azure.idem.vmware.com/v1alpha1
kind: resource-groups
metadata:
  name: new-rg
spec:
  - resource_group_name: new-rg
  - parameters:
      location: eastus
      tags:
        env: new-rg
        Unit: CMBU
