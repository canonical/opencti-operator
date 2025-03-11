# How to Redeploy the OpenCTI Charm

Both the OpenCTI charm and the OpenCTI connector are stateless charms, so you 
can redeploy the OpenCTI charm at any time.

However, one thing to keep in mind is that the newly deployed charm must use the
same Juju application name as the previous OpenCTI charm. This is because the
OpenCTI charm uses the Juju application name as the OpenSearch index prefix. 
Doing so ensures that the new OpenCTI charm inherits the old data created by
the previous charm.
